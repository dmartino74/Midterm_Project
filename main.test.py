from decimal import Decimal
from app.calculation import Calculation
import time

def test_calculation_methods():
    print("\n🔍 Testing Calculation Methods Manually\n")

    # Create a Calculation object
    calc = Calculation(operation="Addition", operand1=Decimal("5"), operand2=Decimal("3"))

    # Run and print each method
    print("describe():", calc.describe())
    print("is_integer_result():", calc.is_integer_result())
    print("round_result(2):", calc.round_result(2))
    print("is_positive():", calc.is_positive())
    print("latex_format():", calc.latex_format())

    # Clone and compare
    clone = calc.clone_with_new_operands(Decimal("10"), Decimal("2"))
    print("clone_with_new_operands():", clone.describe())
    print("is_same_operation():", calc.is_same_operation(clone))

    # Wait and check elapsed time
    time.sleep(1)
    print("elapsed_time():", calc.elapsed_time())

    # Format and serialize
    print("format_result(4):", calc.format_result(4))
    print("to_dict():", calc.to_dict())
    print("to_json():", calc.to_json())

    # Deserialize and compare
    restored = Calculation.from_dict(calc.to_dict())
    print("from_dict():", restored.describe())
    print("__eq__():", calc == restored)

if __name__ == "__main__":
    test_calculation_methods()
    # calculator_repl()  # ← Comment this out while testing
