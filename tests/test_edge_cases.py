import pytest
from decimal import Decimal
from app.calculator import Calculator
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError, ValidationError
from app.operations import OperationFactory

# 🔍 app/calculator.py — test invalid operation name
def test_set_operation_by_name_invalid():
    calc = Calculator()
    with pytest.raises(OperationError):
        calc.set_operation_by_name('invalid_op')

# 🔍 app/calculator.py — test observer notification with no observers
def test_notify_observers_empty():
    calc = Calculator()
    calc.notify_observers(None)  # Should not raise

# 🔍 app/calculator.py — test redo with no undo
def test_redo_without_undo():
    calc = Calculator()
    assert calc.redo() is False

# 🔍 app/calculator.py — test empty history display
def test_show_history_empty():
    calc = Calculator()
    assert calc.show_history() == []

# 🔍 app/calculator_memento.py — restore from empty history
def test_memento_restore_empty():
    memento = CalculatorMemento(history=[])
    assert memento.history == []

# 🔍 app/calculator_memento.py — simulate multiple snapshots
def test_memento_restore_sequence():
    m1 = CalculatorMemento(history=['first'])
    m2 = CalculatorMemento(history=['second'])
    assert m2.history == ['second']
    assert m1.history == ['first']

# 🔍 app/operations.py — root with zero degree
def test_root_zero_degree():
    op = OperationFactory.create_operation('root')
    with pytest.raises(ValidationError):
        op.execute(Decimal('9'), Decimal('0'))

# 🔍 app/operations.py — modulo by zero
def test_modulo_zero_divisor():
    op = OperationFactory.create_operation('mod')
    with pytest.raises(ValidationError):
        op.execute(Decimal('5'), Decimal('0'))

# 🔍 app/operations.py — divide by zero
def test_divide_by_zero():
    op = OperationFactory.create_operation('divide')
    with pytest.raises(ValidationError):
        op.execute(Decimal('10'), Decimal('0'))

# 🔍 app/operations.py — root of negative number with even degree
def test_root_negative_even():
    op = OperationFactory.create_operation('root')
    with pytest.raises(ValidationError):
        op.execute(Decimal('-16'), Decimal('2'))

