# Testing Documentation

## Overview

This document describes the testing strategy and implementation for the AI Travel Agent project. The test suite covers unit tests, integration tests, and end-to-end tests to ensure the reliability and quality of the application.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_collect_preferences.py # collect_preferences tool tests
├── test_flights_finder.py      # flights_finder tool tests
├── test_hotels_finder.py       # hotels_finder tool tests
└── test_agent_workflow.py      # Agent workflow and state management tests
```

## Test Categories

### 1. Unit Tests

#### 1.1 collect_preferences Tool Tests (`test_collect_preferences.py`)

**Purpose**: Test the preference collection and extraction functionality.

**Test Cases**:
- **Complete preference extraction**: Verifies extraction of all required fields (destination, dates, budget, interests)
- **Partial preference extraction**: Tests handling of incomplete user input with missing required fields
- **Preference merge logic**: Validates merging new preferences with existing `current_preferences`
- **JSON parsing error handling**: Tests handling of invalid JSON responses from LLM
- **LLM call failure handling**: Verifies graceful handling when LLM API calls fail
- **Date format validation**: Tests normalization of various date formats (ISO, European, text formats)
- **Budget format validation**: Tests normalization of various budget formats (dict, string with symbols, numbers)
- **Markdown JSON wrapping**: Tests handling of markdown-wrapped JSON responses from LLM
- **Interests field requirement**: Validates that interests field is required for completion

**Key Assertions**:
- `is_complete` flag is set correctly based on required fields
- `missing_fields` list accurately identifies missing information
- `clarification_needed` flag corresponds to completion status
- Preferences are properly normalized and merged

#### 1.2 flights_finder Tool Tests (`test_flights_finder.py`)

**Purpose**: Test flight search functionality using SerpAPI.

**Test Cases**:
- **Normal flight search**: Tests successful flight search with valid parameters
- **Missing required parameters**: Tests handling of missing departure/arrival airports or dates
- **SerpAPI call failure**: Verifies error handling when SerpAPI calls fail
- **Date format validation**: Tests YYYY-MM-DD date format requirements
- **Airport code validation**: Tests IATA airport code format validation
- **Return data structure**: Validates the structure of returned flight data
- **Passenger count parameters**: Tests adults, children, infants parameters
- **Default parameters**: Verifies default values for optional parameters
- **One-way flight search**: Tests flight search without return date

**Key Assertions**:
- SerpAPI is called with correct parameters
- Returned data contains expected flight information fields
- Error conditions are handled gracefully
- Parameter validation works correctly

#### 1.3 hotels_finder Tool Tests (`test_hotels_finder.py`)

**Purpose**: Test hotel search functionality using SerpAPI.

**Test Cases**:
- **Normal hotel search**: Tests successful hotel search with valid parameters
- **Missing required parameters**: Tests handling of missing location or dates
- **SerpAPI call failure**: Verifies error handling when SerpAPI calls fail
- **Date format validation**: Tests YYYY-MM-DD date format requirements
- **Hotel class filtering**: Tests filtering by hotel star rating
- **Sorting functionality**: Tests different sorting options (rating, price)
- **Guest count parameters**: Tests adults, children, rooms parameters
- **Result limiting**: Verifies results are limited to 5 properties
- **Default parameters**: Verifies default values for optional parameters
- **Location parameter variations**: Tests various location format inputs

**Key Assertions**:
- SerpAPI is called with correct parameters
- Results are properly limited to 5 properties
- Hotel class and sorting filters work correctly
- Error conditions are handled appropriately

#### 1.4 Agent Workflow Tests (`test_agent_workflow.py`)

**Purpose**: Test the LangGraph workflow, state management, and tool routing.

**Test Cases**:
- **State transition (call_tools_llm → invoke_tools)**: Tests transition when tool calls exist
- **State transition (call_tools_llm → email_sender)**: Tests transition when no tool calls exist
- **Conditional edge logic (exists_action)**: Tests routing logic based on tool calls
- **Tool invocation routing**: Tests correct tool invocation and parameter passing
- **Bad tool name handling**: Tests handling of invalid tool names from LLM
- **Memory and state management**: Tests state persistence across interactions
- **Preferences state update**: Tests that preferences are properly updated in state
- **Multiple tool invocation**: Tests handling of multiple tool calls in single message
- **Graph structure initialization**: Verifies correct graph node and edge setup
- **Entry point validation**: Tests that graph starts at correct node
- **Interrupt configuration**: Verifies interrupt_before configuration for email_sender
- **Error handling in LLM invocation**: Tests handling of LLM API errors
- **Tool message creation**: Tests correct creation of ToolMessage objects
- **State message accumulation**: Tests that messages are accumulated using operator.add

**Key Assertions**:
- State transitions follow the defined workflow
- Tools are invoked with correct parameters
- Memory/checkpointer maintains state across interactions
- Conditional edges route correctly based on state
- Error conditions don't break the workflow

### 2. Integration Tests

**Status**: Planned for future implementation

**Purpose**: Test complete user flows from input to output.

**Planned Test Cases**:
- Complete travel planning workflow (preferences → flights → hotels → email)
- Multi-turn conversation with preference refinement
- State persistence and recovery
- Error recovery and retry logic

### 3. End-to-End Tests

**Status**: Planned for future implementation

**Purpose**: Test the complete application including Streamlit UI.

**Planned Test Cases**:
- Streamlit UI interaction testing
- Form submission and validation
- Email sending functionality
- User feedback and error display

## Running Tests

### Prerequisites

Install test dependencies:
```bash
poetry install --with dev
```

Set required environment variables (use `.env` file or export):
```bash
OPENAI_API_KEY=your_api_key
SERPAPI_API_KEY=your_serpapi_key
FROM_EMAIL=sender@example.com
TO_EMAIL=recipient@example.com
EMAIL_SUBJECT=Travel Information
SENDGRID_API_KEY=your_sendgrid_key
```

### Run All Tests

```bash
poetry run pytest
```

### Run Specific Test File

```bash
poetry run pytest tests/test_collect_preferences.py
```

### Run Specific Test Function

```bash
poetry run pytest tests/test_collect_preferences.py::TestCollectPreferences::test_complete_preference_extraction
```

### Run with Coverage Report

```bash
poetry run pytest --cov=agents --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run with HTML Report

```bash
poetry run pytest --html=pytest-report.html --self-contained-html
```

### Run by Marker

```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Run only end-to-end tests
poetry run pytest -m e2e

# Skip slow tests
poetry run pytest -m "not slow"
```

### Run in Verbose Mode

```bash
poetry run pytest -v
```

### Run with Specific Output

```bash
# Short traceback format
poetry run pytest --tb=short

# Longer traceback format
poetry run pytest --tb=long

# No traceback (pass/fail only)
poetry run pytest --tb=no
```

## Test Configuration

### pytest.ini

The `pytest.ini` file configures pytest behavior:

- **Test paths**: `tests` directory
- **File patterns**: `test_*.py`
- **Coverage**: Enabled for `agents` module
- **HTML reports**: Enabled with self-contained option
- **Markers**: Defined for different test categories

### conftest.py

Shared fixtures defined in `conftest.py`:

- **mock_env_vars**: Mock environment variables for testing
- **sample_travel_preferences**: Sample preference data
- **sample_flight_data**: Sample flight search results
- **sample_hotel_data**: Sample hotel search results

## Mocking Strategy

### LLM Calls

All LLM calls are mocked using `unittest.mock.patch` to avoid actual API calls and ensure test repeatability.

### External APIs

SerpAPI and SendGrid calls are mocked to:
- Avoid rate limits and costs
- Ensure consistent test results
- Test error conditions without actual failures

### Environment Variables

Environment variables are mocked using `patch.dict(os.environ, ...)` to provide consistent test configuration.

## Test Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Code coverage plugin
- **pytest-mock**: Mocking utilities
- **pytest-asyncio**: Async test support
- **pytest-html**: HTML report generation
- **responses**: HTTP request mocking
- **freezegun**: Time freezing for date-dependent tests

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: poetry run pytest --cov=agents --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Descriptive names**: Test function names should clearly describe what they test
3. **Arrange-Act-Assert**: Structure tests in AAA pattern
4. **Mock external dependencies**: Always mock external API calls
5. **Test edge cases**: Include tests for error conditions and edge cases
6. **Keep tests fast**: Unit tests should run quickly
7. **Maintainability**: Update tests when code changes

## Adding New Tests

When adding new functionality:

1. Create a new test file in `tests/` directory
2. Name it `test_<module_name>.py`
3. Create a test class `Test<ModuleName>`
4. Add test methods starting with `test_`
5. Use descriptive names for test methods
6. Add fixtures to `conftest.py` if they're shared across tests
7. Run the new tests to ensure they pass
8. Update this documentation if needed

## Troubleshooting

### Import Errors

If you encounter import errors, ensure:
- The project root is in the Python path
- You're running tests from the project root directory
- All dependencies are installed: `poetry install`

### Mock Not Working

If mocks aren't being applied:
- Check that the import path in the patch matches the actual import
- Verify the patch is applied before the function is called
- Use `spec=True` to ensure mock matches the real interface

### Tests Timing Out

If tests are timing out:
- Check for actual API calls that should be mocked
- Verify that async tests are using `pytest-asyncio` correctly
- Increase timeout if testing slow operations

## Future Improvements

- [ ] Add integration tests for complete user workflows
- [ ] Add end-to-end tests with Streamlit
- [ ] Add performance tests for API responses
- [ ] Add contract tests for external API integrations
- [ ] Add visual regression tests for UI
- [ ] Add load testing for concurrent users
- [ ] Add security testing for input validation
