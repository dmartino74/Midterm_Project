import pytest
import datetime
import logging
from decimal import Decimal
from app.calculation import Calculation
from app.exceptions import OperationError

# Test division by zero
def test_division_by_zero():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        Calculation("Division", Decimal("5"), Decimal("0"))

# Test negative exponent in power operation
def test_negative_power():
    with pytest.raises(OperationError, match="Negative exponents are not supported"):
        Calculation("Power", Decimal("2"), Decimal("-3"))

# Test root of a negative number
def test_root_of_negative_number():
    with pytest.raises(OperationError, match="Cannot calculate root of negative number"):
        Calculation("Root", Decimal("-4"), Decimal("2"))

# Test zero as root degree
def test_zero_root_degree():
    with pytest.raises(OperationError, match="Zero root is undefined"):
        Calculation("Root", Decimal("4"), Decimal("0"))

# Test mismatched result warning in from_dict
def test_mismatched_result_warning(caplog):
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "999",  # intentionally incorrect
        "timestamp": datetime.datetime.now().isoformat()
    }
    with caplog.at_level(logging.WARNING):
        calc = Calculation.from_dict(data)
        assert "differs from computed result" in caplog.text
