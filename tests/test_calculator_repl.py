import pytest
from unittest.mock import patch
from app.calculator_repl import calculator_repl

# Exit command
@patch('builtins.print')
@patch('builtins.input', side_effect=['exit'])
def test_exit_command(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("Goodbye!")

# Help command
@patch('builtins.print')
@patch('builtins.input', side_effect=['help', 'exit'])
def test_help_command(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

# Addition command
@patch('builtins.print')
@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
def test_addition(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 5")

# Store and recall memory
@patch('builtins.print')
@patch('builtins.input', side_effect=['add', '4', '4', 'store', 'A', 'recall', 'A', 'exit'])
def test_store_and_recall(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("Stored result in slot 'A'")
    mock_print.assert_any_call("Value in 'A': 8")

# Alias definition and usage
@patch('builtins.print')
@patch('builtins.input', side_effect=['alias', 'x', 'exit', 'x'])
def test_alias_command(mock_input, mock_print):
    calculator_repl()
    calls = [call[0][0] for call in mock_print.call_args_list]
    assert any("Alias set: 'x' → 'exit'" in c for c in calls)
    assert any("Goodbye!" in c for c in calls)

# Tutorial command
@patch('builtins.print')
@patch('builtins.input', side_effect=['tutorial', 'exit'])
def test_tutorial_command(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("Welcome to the calculator tutorial...")

# Cancel during input
@patch('builtins.print')
@patch('builtins.input', side_effect=['add', 'cancel', 'exit'])
def test_cancel_first_operand(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("Operation cancelled")

# Unknown command
@patch('builtins.print')
@patch('builtins.input', side_effect=['foobar', 'exit'])
def test_unknown_command(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("Unknown command: 'foobar'. Type 'help' for available commands.")

# Clear memory
@patch('builtins.print')
@patch('builtins.input', side_effect=['clear_memory', 'exit'])
def test_clear_memory_command(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("Memory slots cleared")

# Undo/Redo with no history
@patch('builtins.print')
@patch('builtins.input', side_effect=['undo', 'redo', 'exit'])
def test_undo_redo_empty(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("Nothing to undo")
    mock_print.assert_any_call("Nothing to redo")

# Clear history
@patch('builtins.print')
@patch('builtins.input', side_effect=['clear', 'exit'])
def test_clear_history(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("History cleared")

# Empty history
@patch('builtins.print')
@patch('builtins.input', side_effect=['history', 'exit'])
def test_empty_history(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("No calculations in history")

# Invalid operands
@patch('builtins.print')
@patch('builtins.input', side_effect=['add', 'foo', 'bar', 'exit'])
def test_invalid_operands(mock_input, mock_print):
    calculator_repl()
    assert any("Error:" in call[0][0] for call in mock_print.call_args_list)

# KeyboardInterrupt simulation
@patch('builtins.print')
@patch('builtins.input', side_effect=[KeyboardInterrupt, 'exit'])
def test_keyboard_interrupt(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("\nOperation cancelled")
    mock_print.assert_any_call("Goodbye!")

# EOFError simulation
@patch('builtins.print')
@patch('builtins.input', side_effect=[EOFError])
def test_eof_error(mock_input, mock_print):
    calculator_repl()
    mock_print.assert_any_call("\nInput terminated. Exiting...")
