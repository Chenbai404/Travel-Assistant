"""Test script for preference memory integration."""

import json
import sys
import os
from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.memory.preference_memory import PreferenceMemory, get_preference_memory
from agents.tools.collect_preferences import collect_preferences, PreferenceInput


def test_memory_basic_operations():
    """Test basic memory operations."""
    print("=== Testing Basic Memory Operations ===")
    
    memory = PreferenceMemory(storage_dir="test_data/memory")
    
    # Test user ID
    user_id = "test_user_001"
    
    # Test adding interests
    print("\n1. Adding interests...")
    interests = memory.add_interest(user_id, "coffee")
    print(f"   Interests after adding 'coffee': {interests}")
    
    interests = memory.add_interest(user_id, "museums")
    print(f"   Interests after adding 'museums': {interests}")
    
    # Test getting interests
    print("\n2. Getting interests...")
    retrieved_interests = memory.get_interests(user_id)
    print(f"   Retrieved interests: {retrieved_interests}")
    
    # Test updating preferences
    print("\n3. Updating preferences...")
    preferences = {
        "destination": "Kyoto",
        "interests": ["coffee", "museums", "history"],
        "budget": {"amount": 2000, "currency": "USD"}
    }
    updated = memory.update_user_preferences(user_id, preferences)
    print(f"   Updated preferences: {updated}")
    
    # Test getting preferences
    print("\n4. Getting preferences...")
    retrieved = memory.get_user_preferences(user_id)
    print(f"   Retrieved preferences: {retrieved}")
    
    # Test preference summary
    print("\n5. Getting preference summary...")
    summary = memory.get_preference_summary(user_id)
    print(f"   Summary:\n{summary}")
    
    # Test merge with memory
    print("\n6. Testing merge with memory...")
    current_prefs = {"destination": "Tokyo", "start_date": "2024-03-15"}
    merged = memory.merge_with_memory(user_id, current_prefs)
    print(f"   Merged preferences: {merged}")
    
    # Clean up
    print("\n7. Cleaning up...")
    memory.clear_user_preferences(user_id)
    print("   Test user preferences cleared.")
    
    print("\n=== Basic Memory Operations Test Complete ===\n")


def test_collect_preferences_with_memory():
    """The tool merges persisted preferences without a real LLM call."""

    memory = get_preference_memory()
    user_id = "test_user_002"
    input1 = PreferenceInput(
        user_input="I really love coffee and visiting museums",
        current_preferences=None,
        user_id=user_id
    )
    input2 = PreferenceInput(
        user_input="Help me plan a trip to Kyoto",
        current_preferences=None,
        user_id=user_id
    )

    responses = [
        AIMessage(
            content=json.dumps(
                {
                    "destination": None,
                    "start_date": None,
                    "end_date": None,
                    "budget": None,
                    "interests": ["coffee", "museums"],
                }
            )
        ),
        AIMessage(
            content=json.dumps(
                {
                    "destination": "Kyoto",
                    "start_date": None,
                    "end_date": None,
                    "budget": None,
                    "interests": None,
                }
            )
        ),
    ]

    with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
        mock_llm = Mock()
        mock_llm.invoke.side_effect = responses
        mock_llm_class.return_value = mock_llm

        result1 = collect_preferences.invoke(
            {'params': input1.dict()}
        )
        result2 = collect_preferences.invoke(
            {'params': input2.dict()}
        )

    assert result1['preferences']['interests'] == ['coffee', 'museums']
    assert result2['preferences']['destination'] == 'Kyoto'
    assert result2['preferences']['interests'] == ['coffee', 'museums']

    stored = memory.get_user_preferences(user_id)
    assert stored['destination'] == 'Kyoto'
    assert stored['interests'] == ['coffee', 'museums']


def test_memory_persistence():
    """Test that memory persists across instances."""
    print("=== Testing Memory Persistence ===")
    
    user_id = "test_user_003"
    
    # First instance
    print("\n1. First memory instance...")
    memory1 = PreferenceMemory(storage_dir="test_data/memory")
    memory1.add_interest(user_id, "photography")
    memory1.add_interest(user_id, "nature")
    print(f"   Added interests: photography, nature")
    
    # Second instance (should read from same storage)
    print("\n2. Second memory instance (reading from storage)...")
    memory2 = PreferenceMemory(storage_dir="test_data/memory")
    interests = memory2.get_interests(user_id)
    print(f"   Retrieved interests: {interests}")
    
    # Verify persistence
    if "photography" in interests and "nature" in interests:
        print("   ✅ Memory persistence successful!")
    else:
        print("   ❌ Memory persistence failed!")
    
    # Clean up
    memory2.clear_user_preferences(user_id)
    print("\n3. Cleaned up test data.")
    
    print("\n=== Memory Persistence Test Complete ===\n")


if __name__ == "__main__":
    print("Starting Preference Memory Integration Tests\n")
    
    try:
        test_memory_basic_operations()
        test_collect_preferences_with_memory()
        test_memory_persistence()
        
        print("\n" + "="*50)
        print("All tests completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
