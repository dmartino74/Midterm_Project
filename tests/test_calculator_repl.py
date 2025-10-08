import pytest
from unittest.mock import patch
from app.calculator_repl import calculator_repl

# Test help command
@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_help_command(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

# Test addition
@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
def test_addition(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 5")

# Test storing and recalling memory
@patch('builtins.input', side_effect=['add', '4', '4', 'store', 'A', 'recall', 'A', 'exit'])
@patch('builtins.print')
def test_store_and_recall(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Stored result in slot 'A'")
    mock_print.assert_any_call("Value in 'A': 8")

# Test alias definition and usage
@patch('builtins.input', side_effect=['alias', 'x', 'exit', 'x'])
@patch('builtins.print')
def test_alias_command(mock_print, mock_input):
    calculator_repl()
    calls = [call[0][0] for call in mock_print.call_args_list]
    assert any("Alias set: 'x' → 'exit'" in c for c in calls)
    assert any("Goodbye!" in c for c in calls)

# Test tutorial
@patch('builtins.input', side_effect=['tutorial', 'exit'])
@patch('builtins.print')
def test_tutorial_command(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Welcome to the calculator tutorial...")

# Test cancel during input
@patch('builtins.input', side_effect=['add', 'cancel', 'exit'])
@patch('builtins.print')
def test_cancel_first_operand(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation cancelled")

# Test unknown command
@patch('builtins.input', side_effect=['foobar', 'exit'])
@patch('builtins.print')
def test_unknown_command(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Unknown command: 'foobar'. Type 'help' for available commands.")
