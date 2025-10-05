from decimal import Decimal
import logging

# Import core modules and design pattern components
from app.calculator import Calculator              # Facade Pattern: central interface
from app.exceptions import OperationError, ValidationError  # Custom error types
from app.history import AutoSaveObserver, LoggingObserver   # Observer Pattern
from app.operations import OperationFactory        # Factory Pattern

def calculator_repl():
    """
    REPL (Read-Eval-Print Loop) for the calculator with essential and enhanced commands.
    """
    try:
        calc = Calculator()
        calc.add_observer(LoggingObserver())
        calc.add_observer(AutoSaveObserver(calc))

        calc.last_result = None  # ✅ Ensure last_result is initialized

        print("Calculator started. Type 'help' for commands.")

        aliases = {"q": "exit", "h": "help", "m": "multiply"}
        memory = {}

        while True:
            try:
                command = input("\nEnter command: ").lower().strip()
                command = aliases.get(command, command)

                if command == 'help':
                    print("\nAvailable commands:")
                    print("  add, subtract, multiply, divide, power, root, mod - Perform calculations")
                    print("  history - Show calculation history")
                    print("  clear - Clear calculation history")
                    print("  undo - Undo the last calculation")
                    print("  redo - Redo the last undone calculation")
                    print("  store - Store result in memory slot")
                    print("  recall - Recall value from memory slot")
                    print("  clear_memory - Clear all memory slots")
                    print("  alias - Define command shortcut")
                    print("  tutorial - Walkthrough of features")
                    print("  exit - Exit the calculator")
                    continue

                if command == 'exit':
                    calc.save_history()  # ✅ Save history before exiting
                    print("Goodbye!")
                    break

                if command == 'history':
                    history = calc.show_history()
                    if not history:
                        print("No calculations in history")
                    else:
                        print("\nCalculation History:")
                        for i, entry in enumerate(history, 1):
                            print(f"{i}. {entry}")
                    continue

                if command == 'clear':
                    calc.clear_history()
                    print("History cleared")
                    continue

                if command == 'undo':
                    print("Operation undone" if calc.undo() else "Nothing to undo")
                    continue

                if command == 'redo':
                    print("Operation redone" if calc.redo() else "Nothing to redo")
                    continue

                if command == 'store':
                    slot = input("Enter memory slot name (e.g., A): ").strip()
                    memory[slot] = calc.last_result
                    print(f"Stored result in slot '{slot}'")
                    continue

                if command == 'recall':
                    slot = input("Enter memory slot name to recall: ").strip()
                    value = memory.get(slot)
                    print(f"Value in '{slot}': {value}" if value else f"No value stored in '{slot}'")
                    continue

                if command == 'clear_memory':
                    memory.clear()
                    print("Memory slots cleared")
                    continue

                if command == 'alias':
                    shortcut = input("Enter shortcut (e.g., q): ").strip()
                    full = input("Enter full command (e.g., exit): ").strip()
                    aliases[shortcut] = full
                    print(f"Alias set: '{shortcut}' → '{full}'")
                    continue

                if command == 'tutorial':
                    print("Welcome to the calculator tutorial...")
                    print("Try typing 'add' to begin a calculation.")
                    print("Use 'history' to view past results, and 'undo' to reverse mistakes.")
                    continue

                if command in ['add', 'subtract', 'multiply', 'divide', 'power', 'root', 'mod']:
                    try:
                        print("\nEnter numbers (or 'cancel' to abort):")
                        a = input("First number: ")
                        if a.lower() == 'cancel':
                            print("Operation cancelled")
                            continue
                        b = input("Second number: ")
                        if b.lower() == 'cancel':
                            print("Operation cancelled")
                            continue

                        operation = OperationFactory.create_operation(command)
                        calc.set_operation(operation)

                        result = calc.perform_operation(a, b)

                        if isinstance(result, Decimal):
                            result = result.normalize()

                        calc.last_result = result
                        print(f"\nResult: {result}")
                    except (ValidationError, OperationError) as e:
                        print(f"Error: {e}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                    continue

                print(f"Unknown command: '{command}'. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\nOperation cancelled")
                continue
            except EOFError:
                print("\nInput terminated. Exiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue

    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error in calculator REPL: {e}")
        raise
