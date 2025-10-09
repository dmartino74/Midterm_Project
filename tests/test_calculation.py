import pytest
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from app.calculation import Calculation
from app.exceptions import OperationError

# Core operations
def test_addition():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    assert calc.result == Decimal("5")

def test_subtraction():
    calc = Calculation("Subtraction", Decimal("5"), Decimal("3"))
    assert calc.result == Decimal("2")

def test_multiplication():
    calc = Calculation("Multiplication", Decimal("4"), Decimal("2"))
    assert calc.result == Decimal("8")

def test_division():
    calc = Calculation("Division", Decimal("8"), Decimal("2"))
    assert calc.result == Decimal("4")

def test_division_by_zero():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        Calculation("Division", Decimal("8"), Decimal("0"))

def test_power():
    calc = Calculation("Power", Decimal("2"), Decimal("3"))
    assert calc.result == Decimal("8")

def test_negative_power():
    with pytest.raises(OperationError, match="Negative exponents are not supported"):
        Calculation("Power", Decimal("2"), Decimal("-3"))

def test_root():
    calc = Calculation("Root", Decimal("16"), Decimal("2"))
    assert calc.result == Decimal("4")

def test_invalid_root_negative():
    with pytest.raises(OperationError, match="Cannot calculate root of negative number"):
        Calculation("Root", Decimal("-16"), Decimal("2"))

def test_invalid_root_zero():
    with pytest.raises(OperationError, match="Zero root is undefined"):
        Calculation("Root", Decimal("16"), Decimal("0"))

def test_modulo():
    calc = Calculation("Modulo", Decimal("10"), Decimal("3"))
    assert calc.result == Decimal("1")

def test_modulo_by_zero():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        Calculation("Modulo", Decimal("10"), Decimal("0"))

def test_unknown_operation():
    with pytest.raises(OperationError, match="Unknown operation"):
        Calculation("Unknown", Decimal("5"), Decimal("3"))

# Helper method coverage
def test_raise_div_zero():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        Calculation("Division", Decimal("1"), Decimal("0"))

def test_raise_neg_power():
    with pytest.raises(OperationError, match="Negative exponents are not supported"):
        Calculation("Power", Decimal("2"), Decimal("-1"))

def test_raise_zero_root():
    with pytest.raises(OperationError, match="Zero root is undefined"):
        Calculation("Root", Decimal("9"), Decimal("0"))

def test_raise_negative_root():
    with pytest.raises(OperationError, match="Cannot calculate root of negative number"):
        Calculation("Root", Decimal("-9"), Decimal("2"))

# Serialization
def test_to_dict():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    result_dict = calc.to_dict()
    assert result_dict == {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": calc.timestamp.isoformat()
    }

def test_to_json():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    json_str = calc.to_json()
    assert '"operation": "Addition"' in json_str
    assert '"result": "5"' in json_str

def test_from_dict():
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": datetime.now().isoformat()
    }
    calc = Calculation.from_dict(data)
    assert calc.operation == "Addition"
    assert calc.operand1 == Decimal("2")
    assert calc.operand2 == Decimal("3")
    assert calc.result == Decimal("5")

def test_invalid_from_dict():
    data = {
        "operation": "Addition",
        "operand1": "invalid",
        "operand2": "3",
        "result": "5",
        "timestamp": datetime.now().isoformat()
    }
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(data)

def test_missing_keys_from_dict():
    data = {
        "operation": "Addition",
        "operand1": "2",
        "result": "5",
        "timestamp": datetime.now().isoformat()
    }
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(data)

def test_bad_timestamp_from_dict():
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": "not-a-valid-timestamp"
    }
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(data)

def test_from_dict_result_mismatch(caplog):
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "10",
        "timestamp": datetime.now().isoformat()
    }
    with caplog.at_level(logging.WARNING):
        calc = Calculation.from_dict(data)
    assert "Loaded calculation result 10 differs from computed result 5" in caplog.text

# Utility methods
def test_format_result():
    calc = Calculation("Division", Decimal("1"), Decimal("3"))
    assert calc.format_result(precision=2) == "0.33"
    assert calc.format_result(precision=10) == "0.3333333333"

def test_format_result_default():
    calc = Calculation("Addition", Decimal("1"), Decimal("2"))
    assert calc.format_result() == "3"

def test_format_result_fallback():
    calc = Calculation("Addition", Decimal("1"), Decimal("2"))
    calc.result = Decimal("NaN")
    assert calc.format_result(2) == "NaN"

def test_is_integer_result():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    assert calc.is_integer_result() is True

def test_round_result():
    calc = Calculation("Division", Decimal("10"), Decimal("3"))
    assert calc.round_result(2) == Decimal("3.33")

def test_is_positive():
    calc = Calculation("Subtraction", Decimal("5"), Decimal("3"))
    assert calc.is_positive() is True

def test_describe():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    assert calc.describe() == "2 Addition 3 = 5"

def test_latex_format():
    calc = Calculation("Multiplication", Decimal("2"), Decimal("3"))
    assert calc.latex_format() == "$2 \\times 3 = 6$"

def test_clone_with_new_operands():
    original = Calculation("Addition", Decimal("2"), Decimal("3"))
    clone = original.clone_with_new_operands(Decimal("10"), Decimal("5"))
    assert clone.operation == "Addition"
    assert clone.operand1 == Decimal("10")
    assert clone.operand2 == Decimal("5")

def test_is_same_operation():
    calc1 = Calculation("Addition", Decimal("2"), Decimal("3"))
    calc2 = Calculation("Addition", Decimal("10"), Decimal("5"))
    calc3 = Calculation("Subtraction", Decimal("10"), Decimal("5"))
    assert calc1.is_same_operation(calc2) is True
    assert calc1.is_same_operation(calc3) is False

def test_elapsed_time():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    elapsed = calc.elapsed_time()
    assert isinstance(elapsed, timedelta)
    assert elapsed.total_seconds() >= 0

# Equality and representation
def test_equality():
    calc1 = Calculation("Addition", Decimal("2"), Decimal("3"))
    calc2 = Calculation("Addition", Decimal("2"), Decimal("3"))
    calc3 = Calculation("Subtraction", Decimal("5"), Decimal("3"))
    assert calc1 == calc2
    assert calc1 != calc3

def test_equality_with_non_calculation():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    assert calc != "not a calculation"

def test_str_and_repr():
    calc = Calculation("Addition", Decimal("2"), Decimal("3"))
    assert str(calc) == "Addition(2, 3) = 5"
    expected_repr = (
        f"Calculation(operation='Addition', operand1={calc.operand1}, "
        f"operand2={calc.operand2}, result={calc.result}, "
        f"timestamp='{calc.timestamp.isoformat()}')"
    )
    assert repr(calc) == expected_repr
