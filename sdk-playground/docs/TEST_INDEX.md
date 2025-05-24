# Test Index

This document serves as a practical reference for running tests and maintaining test coverage. It provides quick access to test locations, dependencies, and common commands.

## File Mappings

### UI Components

| Source File | Test Files | Description |
|------------|------------|-------------|
| `src/ui/app.py` | - `tests/ui/test_app.py`<br>- `tests/integration/test_app_integration.py` | Main application tests including routing and state management |
| `src/ui/components/conversation_turn.py` | `tests/ui/test_conversation_turn.py` | Chat bubble rendering and interaction tests |
| `src/ui/components/metrics_display.py` | `tests/ui/test_metrics_display.py` | Evaluation metrics visualization tests |
| `src/ui/components/main_layout.py` | `tests/ui/test_main_layout.py` | Layout management and navigation tests |
| `src/ui/components/context_viewer.py` | `tests/ui/test_context_viewer.py` | Context display and interaction tests |
| `src/ui/components/conversation_selector.py` | `tests/ui/test_conversation_selector.py` | Conversation selection and filtering tests |
| `src/ui/dashboard.py` | `tests/ui/test_dashboard.py` | Dashboard view and metrics overview tests |

### Services

| Source File | Test Files | Description |
|------------|------------|-------------|
| `src/services/evaluation.py` | - `tests/services/test_evaluation.py`<br>- `tests/integration/test_evaluation_integration.py` | Evaluation service tests including both mock and real modes |
| `src/api/endpoints.py` | - `tests/api/test_endpoints.py`<br>- `tests/integration/test_api_integration.py` | API endpoint tests including request handling |

### Models

| Source File | Test Files | Description |
|------------|------------|-------------|
| `src/models/base.py` | `tests/models/test_base.py` | Base model functionality tests |
| `src/models/context.py` | `tests/models/test_context.py` | Context model tests |
| `src/models/conversation.py` | `tests/models/test_conversation.py` | Conversation model and turn management tests |

### Data Generation

| Source File | Test Files | Description |
|------------|------------|-------------|
| `src/data/dataset_generator.py` | - `tests/data/test_dataset_generator.py`<br>- `tests/integration/test_dataset_integration.py` | Dataset generation and validation tests |

## Common Test Commands

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific component tests
pytest tests/ui/test_app.py -v
pytest tests/services/test_evaluation.py -v
pytest tests/models/test_conversation.py -v

# Run with coverage
pytest --cov=src tests/ -v
pytest --cov=src.ui tests/ui/ -v
pytest --cov=src.services tests/services/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Coverage Analysis

```bash
# Generate coverage report
pytest --cov=src --cov-report=html tests/

# Check coverage for specific module
pytest --cov=src.ui.app --cov-report=term-missing tests/ui/test_app.py
```

## Test Dependencies

### UI Changes
When modifying UI components:
1. Run component tests:
   ```bash
   pytest tests/ui/test_<component>.py -v
   ```
2. Run integration tests:
   ```bash
   pytest tests/integration/test_app_integration.py -v
   ```

### Service Changes
When modifying services:
1. Run service tests:
   ```bash
   pytest tests/services/test_<service>.py -v
   ```
2. Run integration tests:
   ```bash
   pytest tests/integration/ -v
   ```

### Model Changes
When modifying models:
1. Run model tests:
   ```bash
   pytest tests/models/test_<model>.py -v
   ```
2. Run dependent service tests:
   ```bash
   pytest tests/services/ -v
   ```

### Data Generation Changes
When modifying data generation:
1. Run generator tests:
   ```bash
   pytest tests/data/test_dataset_generator.py -v
   ```
2. Run integration tests:
   ```bash
   pytest tests/integration/ -v
   ```

## Critical Test Paths

### Evaluation Flow
When modifying evaluation-related code:
1. `tests/services/test_evaluation.py`
2. `tests/ui/test_metrics_display.py`
3. `tests/integration/test_evaluation_integration.py`

### Conversation Flow
When modifying conversation display:
1. `tests/ui/test_conversation_turn.py`
2. `tests/ui/test_main_layout.py`
3. `tests/integration/test_app_integration.py`

## Maintaining Test Quality

### When Adding New Features
1. Add corresponding test files
2. Update this index
3. Ensure coverage meets requirements:
   - Unit Tests: 90%
   - Integration Tests: 80%
   - UI Tests: 70%

### When Fixing Bugs
1. Add regression tests
2. Run related test paths
3. Update test data if needed

### Regular Maintenance
1. Run full test suite daily
2. Review coverage weekly
3. Update test data monthly
4. Fix flaky tests immediately 