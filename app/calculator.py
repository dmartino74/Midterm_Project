from decimal import Decimal
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# Core modules and design pattern components
from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError, ValidationError
from app.history import HistoryObserver
from app.input_validators import InputValidator
from app.operations import Operation, OperationFactory  # Factory Pattern

# Type aliases for clarity
Number = Union[int, float, Decimal]
CalculationResult = Union[Number, str]

class Calculator:
    """
    Main calculator class implementing multiple design patterns:
    - Strategy: switchable operation logic
    - Observer: notify external components on calculation
    - Memento: undo/redo via history snapshots
    - Facade: unified interface for REPL and tests
    """

    def __init__(self, config: Optional[CalculatorConfig] = None):
        # Load default config if none provided
        if config is None:
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            config = CalculatorConfig(base_dir=project_root)

        self.config = config
        self.config.validate()

        # Ensure logging directory exists
        os.makedirs(self.config.log_dir, exist_ok=True)
        self._setup_logging()

        # Core state
        self.history: List[Calculation] = []  # Stores all calculations
        self.operation_strategy: Optional[Operation] = None  # Strategy pattern
        self.observers: List[HistoryObserver] = []  # Observer pattern
        self.undo_stack: List[CalculatorMemento] = []  # Memento pattern
        self.redo_stack: List[CalculatorMemento] = []

        self._setup_directories()

        # Try loading saved history from CSV
        try:
            self.load_history()
        except Exception as e:
            logging.warning(f"Could not load existing history: {e}")

        logging.info("Calculator initialized with configuration")

    def _setup_logging(self) -> None:
        """
        Configure logging to file with timestamped entries.
        """
        try:
            os.makedirs(self.config.log_dir, exist_ok=True)
            log_file = self.config.log_file.resolve()
            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                force=True
            )
            logging.info(f"Logging initialized at: {log_file}")
        except Exception as e:
            print(f"Error setting up logging: {e}")
            raise

    def _setup_directories(self) -> None:
        """
        Ensure history directory exists for saving CSV files.
        """
        self.config.history_dir.mkdir(parents=True, exist_ok=True)

    def add_observer(self, observer: HistoryObserver) -> None:
        """
        Register an observer to be notified after each calculation.
        """
        self.observers.append(observer)
        logging.info(f"Added observer: {observer.__class__.__name__}")

    def remove_observer(self, observer: HistoryObserver) -> None:
        """
        Unregister an observer.
        """
        self.observers.remove(observer)
        logging.info(f"Removed observer: {observer.__class__.__name__}")

    def notify_observers(self, calculation: Calculation) -> None:
        """
        Notify all observers with the latest calculation.
        """
        for observer in self.observers:
            observer.update(calculation)

    def set_operation(self, operation: Operation) -> None:
        """
        Set the current operation strategy (e.g., add, divide).
        """
        self.operation_strategy = operation
        logging.info(f"Set operation: {operation}")

    def set_operation_by_name(self, name: str) -> None:
        """
        Set operation strategy by string name using OperationFactory.
        Raises OperationError if name is invalid.
        """
        try:
            operation = OperationFactory.create_operation(name)
            self.set_operation(operation)
        except ValueError as e:
            raise OperationError(f"Invalid operation: {name}") from e

    def perform_operation(self, a: Union[str, Number], b: Union[str, Number]) -> CalculationResult:
        """
        Validate inputs, execute operation, update history, notify observers.
        """
        if not self.operation_strategy:
            raise OperationError("No operation set")

        try:
            # Validate and convert inputs
            validated_a = InputValidator.validate_number(a, self.config)
            validated_b = InputValidator.validate_number(b, self.config)

            # Execute strategy
            result = self.operation_strategy.execute(validated_a, validated_b)

            # Create Calculation object
            calculation = Calculation(
                operation=str(self.operation_strategy),
                operand1=validated_a,
                operand2=validated_b
            )

            # Save current state for undo
            self.undo_stack.append(CalculatorMemento(self.history.copy()))
            self.redo_stack.clear()

            # Add to history
            self.history.append(calculation)

            # Trim history if too long
            if len(self.history) > self.config.max_history_size:
                self.history.pop(0)

            # Notify observers
            self.notify_observers(calculation)

            return result

        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Operation failed: {str(e)}")
            raise OperationError(f"Operation failed: {str(e)}")

    def save_history(self) -> None:
        """
        Save history to CSV using pandas.
        """
        try:
            self.config.history_dir.mkdir(parents=True, exist_ok=True)

            history_data = [
                {
                    'operation': str(calc.operation),
                    'operand1': str(calc.operand1),
                    'operand2': str(calc.operand2),
                    'result': str(calc.result),
                    'timestamp': calc.timestamp.isoformat()
                }
                for calc in self.history
            ]

            if history_data:
                df = pd.DataFrame(history_data)
                df.to_csv(self.config.history_file, index=False)
                logging.info(f"History saved successfully to {self.config.history_file}")
            else:
                # Save empty CSV with headers
                pd.DataFrame(columns=['operation', 'operand1', 'operand2', 'result', 'timestamp']
                ).to_csv(self.config.history_file, index=False)
                logging.info("Empty history saved")

        except Exception as e:
            logging.error(f"Failed to save history: {e}")
            raise OperationError(f"Failed to save history: {e}")

    def load_history(self) -> None:
        """
        Load history from CSV and reconstruct Calculation objects.
        """
        try:
            if self.config.history_file.exists():
                df = pd.read_csv(self.config.history_file)
                if not df.empty:
                    self.history = [
                        Calculation.from_dict({
                            'operation': row['operation'],
                            'operand1': row['operand1'],
                            'operand2': row['operand2'],
                            'result': row['result'],
                            'timestamp': row['timestamp']
                        })
                        for _, row in df.iterrows()
                    ]
                    logging.info(f"Loaded {len(self.history)} calculations from history")
                else:
                    logging.info("Loaded empty history file")
            else:
                logging.info("No history file found - starting with empty history")
        except Exception as e:
            logging.error(f"Failed to load history: {e}")
            raise OperationError(f"Failed to load history: {e}")

    def get_history_dataframe(self) -> pd.DataFrame:
        """
        Return history as a pandas DataFrame.
        Useful for analysis or export.
        """
        history_data = [
            {
                'operation': str(calc.operation),
                'operand1': str(calc.operand1),
                'operand2': str(calc.operand2),
                'result': str(calc.result),
                'timestamp': calc.timestamp
            }
            for calc in self.history
        ]
        return pd.DataFrame(history_data)

    def show_history(self) -> List[str]:
        """
        Return history as formatted strings for display.
        """
        return [
            f"{calc.operation}({calc.operand1}, {calc.operand2}) = {calc.result}"
            for calc in self.history
        ]

    def clear_history(self) -> None:
        """
        Clear history and undo/redo stacks.
        """
        self.history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        logging.info("History cleared")

    def undo(self) -> bool:
        """
        Restore previous history state from undo stack.
        Returns True if successful.
        """
        if not self.undo_stack:
            return False
        memento = self.undo_stack.pop()
        self.redo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True

    def redo(self) -> bool:
        """
        Reapply undone history state from redo stack.
        Returns True if successful.
        """
        if not self.redo_stack:
            return False
        memento = self.redo_stack.pop()
        self.undo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True
