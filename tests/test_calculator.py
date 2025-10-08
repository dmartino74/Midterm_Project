import datetime
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import Mock, patch, PropertyMock
from decimal import Decimal
from tempfile import TemporaryDirectory
from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
from app.history import LoggingObserver
from app.operations import OperationFactory

# Fixture to initialize Calculator with a temporary directory for file paths
@pytest.fixture
def calculator():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)

        with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
             patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
             patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
             patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:

            mock_log_dir.return_value = temp_path / "logs"
            mock_log_file.return_value = temp_path / "logs/calculator.log"
            mock_history_dir.return_value = temp_path / "history"
            mock_history_file.return_value = temp_path / "history/calculator_history.csv"

            yield Calculator(config=config)

# Initialization and Logging
def test_calculator_initialization(calculator):
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []
    assert calculator.operation_strategy is None

@patch('app.calculator.logging.info')
def test_calculator_initialization_logs(mock_log):
    Calculator(CalculatorConfig())
    mock_log.assert_any_call("Calculator initialized with configuration")

@patch('app.calculator.os.makedirs', side_effect=OSError("Permission denied"))
def test_logging_setup_failure(mock_makedirs):
    config = CalculatorConfig(base_dir=Path('/invalid/path'))
    with pytest.raises(OSError, match="Permission denied"):
        Calculator(config)

# Observer Pattern
def test_add_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    assert observer in calculator.observers

@patch('app.calculator.logging.info')
def test_add_observer_logs(mock_log, calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    mock_log.assert_any_call("Added observer: LoggingObserver")

def test_remove_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    assert observer not in calculator.observers

# Operation Strategy
def test_set_operation(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    assert calculator.operation_strategy == operation

# Operation Execution
def test_perform_operation_addition(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    result = calculator.perform_operation(2, 3)
    assert result == Decimal('5')

def test_perform_operation_validation_error(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    with pytest.raises(ValidationError):
        calculator.perform_operation('invalid', 3)

def test_perform_operation_operation_error(calculator):
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(2, 3)

def test_perform_operation_execution_failure(calculator):
    class FailingOperation:
        def execute(self, a, b): raise RuntimeError("Boom")
        def __str__(self): return "FailOp"
    calculator.set_operation(FailingOperation())
    with pytest.raises(OperationError, match="Operation failed: Boom"):
        calculator.perform_operation(2, 3)

# Undo/Redo
def test_undo(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    calculator.undo()
    assert calculator.history == []

def test_redo(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    calculator.undo()
    calculator.redo()
    assert len(calculator.history) == 1

# History Saving and Loading
@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history(mock_to_csv, calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    calculator.save_history()
    mock_to_csv.assert_called_once()

@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_empty_history(mock_to_csv, calculator):
    calculator.save_history()
    mock_to_csv.assert_called_once()

@patch('app.calculator.pd.DataFrame.to_csv', side_effect=OSError("Write error"))
def test_save_history_failure(mock_to_csv, calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    with pytest.raises(OperationError, match="Failed to save history: Write error"):
        calculator.save_history()

@patch('app.calculator.pd.read_csv')
@patch('app.calculator.Path.exists', return_value=True)
def test_load_history(mock_exists, mock_read_csv, calculator):
    mock_read_csv.return_value = pd.DataFrame({
        'operation': ['Addition'],
        'operand1': ['2'],
        'operand2': ['3'],
        'result': ['5'],
        'timestamp': [datetime.datetime.now().isoformat()]
    })
    calculator.load_history()
    assert len(calculator.history) == 1
    assert calculator.history[0].operation == "Addition"

@patch('app.calculator.pd.read_csv', side_effect=OSError("Read error"))
@patch('app.calculator.Path.exists', return_value=True)
def test_load_history_failure(mock_exists, mock_read_csv, calculator):
    with pytest.raises(OperationError, match="Failed to load history: Read error"):
        calculator.load_history()

# History Accessors
def test_get_history_dataframe(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    df = calculator.get_history_dataframe()
    assert not df.empty

def test_show_history(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    history = calculator.show_history()
    assert "Addition(2, 3) = 5" in history[0]

# Clear History
def test_clear_history(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(2, 3)
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []

@patch('app.calculator.logging.info')
def test_clear_history_logs(mock_log, calculator):
    calculator.clear_history()
    mock_log.assert_any_call("History cleared")

# REPL Integration
@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_calculator_repl_exit(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history') as mock_save_history:
        calculator_repl()
        mock_save_history.assert_called_once()
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_calculator_repl_help(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
def test_calculator_repl_addition(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 5")
