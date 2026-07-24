"""Simple test script for preference memory (without langchain dependencies)."""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.memory.preference_memory import PreferenceMemory, get_preference_memory


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
        print("   [OK] Memory persistence successful!")
    else:
        print("   [FAIL] Memory persistence failed!")
    
    # Clean up
    memory2.clear_user_preferences(user_id)
    print("\n3. Cleaned up test data.")
    
    print("\n=== Memory Persistence Test Complete ===\n")


def test_memory_scenario():
    """Test the scenario described by the user."""
    print("=== Testing User Scenario ===")
    
    memory = PreferenceMemory(storage_dir="test_data/memory")
    user_id = "user_scenario_test"
    
    # First interaction: User says "I like coffee"
    print("\n1. First interaction: 'I like coffee'")
    memory.add_interest(user_id, "coffee")
    stored = memory.get_user_preferences(user_id)
    print(f"   Stored preferences: {stored}")
    
    # Second interaction: User asks "Help me plan Kyoto"
    print("\n2. Second interaction: 'Help me plan Kyoto'")
    # Simulate what would happen in collect_preferences
    current_input = {"destination": "Kyoto"}
    merged = memory.merge_with_memory(user_id, current_input)
    print(f"   Merged with memory: {merged}")
    print(f"   Destination: {merged.get('destination')}")
    print(f"   Interests from memory: {merged.get('interests')}")
    
    # Verify the scenario works as expected
    if merged.get('destination') == 'Kyoto' and 'coffee' in merged.get('interests', []):
        print("   [OK] Scenario successful! Agent knows interests=['coffee'] from previous interaction")
    else:
        print("   [FAIL] Scenario failed!")
    
    # Clean up
    memory.clear_user_preferences(user_id)
    print("\n3. Cleaned up test data.")
    
    print("\n=== User Scenario Test Complete ===\n")


if __name__ == "__main__":
    print("Starting Preference Memory Tests\n")
    
    try:
        test_memory_basic_operations()
        test_memory_persistence()
        test_memory_scenario()
        
        print("\n" + "="*50)
        print("All tests completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
