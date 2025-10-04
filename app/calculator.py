########################
# Calculator Class      #
########################

from decimal import Decimal
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError, ValidationError
from app.history import HistoryObserver
from app.input_validators import InputValidator
from app.operations import Operation

# Type aliases for better readability
Number = Union[int, float, Decimal]
CalculationResult = Union[Number, str]


class Calculator:
    """
    Main calculator class implementing multiple design patterns.

    This class serves as the core of the calculator application, managing operations,
    calculation history, observers, configuration settings, and data persistence.
    It integrates various design patterns to enhance flexibility, maintainability, and
    scalability.
    """

    def __init__(self, config: Optional[CalculatorConfig] = None):
        """
        Initialize calculator with configuration.

        Args:
            config (Optional[CalculatorConfig], optional): Configuration settings for the calculator.
                If not provided, default settings are loaded based on environment variables.
        """
        if config is None:
            # Determine the project root directory if no configuration is provided
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            config = CalculatorConfig(base_dir=project_root)

        # Assign the configuration and validate its parameters
        self.config = config
        self.config.validate()

        # Ensure that the log directory exists
        os.makedirs(self.config.log_dir, exist_ok=True)

        # Set up the logging system
        self._setup_logging()

        # Initialize calculation history and operation strategy
        self.history: List[Calculation] = []
        self.operation_strategy: Optional[Operation] = None

        # Initialize observer list for the Observer pattern
        self.observers: List[HistoryObserver] = []

        # Initialize stacks for undo and redo functionality using the Memento pattern
        self.undo_stack: List[CalculatorMemento] = []
        self.redo_stack: List[CalculatorMemento] = []

        # Create required directories for history management
        self._setup_directories()

        try:
            # Attempt to load existing calculation history from file
            self.load_history()
        except Exception as e:
            # Log a warning if history could not be loaded
            logging.warning(f"Could not load existing history: {e}")

        # Log the successful initialization of the calculator
        logging.info("Calculator initialized with configuration")

    def _setup_logging(self) -> None:
        """Configure the logging system."""
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
        """Create required directories."""
        self.config.history_dir.mkdir(parents=True, exist_ok=True)

    # --------------------
    # Observer pattern
    # --------------------
    def add_observer(self, observer: HistoryObserver) -> None:
        """Register a new observer."""
        self.observers.append(observer)
        logging.info(f"Added observer: {observer.__class__.__name__}")

    def remove_observer(self, observer: HistoryObserver) -> None:
        """Remove an existing observer."""
        self.observers.remove(observer)
        logging.info(f"Removed observer: {observer.__class__.__name__}")

    def notify_observers(self, calculation: Calculation) -> None:
        """Notify all observers of a new calculation."""
        for observer in self.observers:
            try:
                observer.update(calculation)
            except Exception as e:
                logging.error(f"Observer {observer.__class__.__name__} failed: {e}")

    # --------------------
    # Strategy pattern
    # --------------------
    def set_operation(self, operation: Operation) -> None:
        """Set the current operation strategy."""
        self.operation_strategy = operation
        logging.info(f"Set operation: {operation}")

    def perform_operation(
        self,
        a: Union[str, Number],
        b: Union[str, Number]
    ) -> CalculationResult:
        """
        Perform calculation with the current operation.
        """
        if not self.operation_strategy:
            raise OperationError("No operation set")

        try:
            validated_a = InputValidator.validate_number(a, self.config)
            validated_b = InputValidator.validate_number(b, self.config)

            # Execute the operation strategy
            result = self.operation_strategy.execute(validated_a, validated_b)

            # Create a new Calculation
            calculation = Calculation(
                operation=str(self.operation_strategy),
                operand1=validated_a,
                operand2=validated_b
            )

            # Save state to undo stack
            self.undo_stack.append(CalculatorMemento(self.history.copy()))
            self.redo_stack.clear()

            # Append new calculation to history
            self.history.append(calculation)

            # Trim history if too large
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

    # --------------------
    # Extra helper methods
    # --------------------
    def get_last_calculation(self) -> Optional[Calculation]:
        """Return the most recent calculation, or None if history is empty."""
        return self.history[-1] if self.history else None

    def perform_with_last(self, b: Union[str, Number]) -> CalculationResult:
        """
        Perform an operation using the result of the last calculation as the first operand.
        """
        last_calc = self.get_last_calculation()
        if not last_calc:
            raise OperationError("No previous calculation to use as the first operand")

        return self.perform_operation(last_calc.result, b)

    def reset(self) -> None:
        """Reset the calculator completely, clearing history, stacks, and observers."""
        self.history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.observers.clear()
        self.operation_strategy = None
        logging.info("Calculator reset to initial state")

    # --------------------
    # Persistence
    # --------------------
    def save_history(self) -> None:
        """Save calculation history to a CSV file using pandas."""
        try:
            self.config.history_dir.mkdir(parents=True, exist_ok=True)
            history_data = [calc.to_dict() for calc in self.history]

            if history_data:
                df = pd.DataFrame(history_data)
                df.to_csv(self.config.history_file, index=False)
                logging.info(f"History saved successfully to {self.config.history_file}")
            else:
                pd.DataFrame(columns=['operation', 'operand1', 'operand2', 'result', 'timestamp']
                           ).to_csv(self.config.history_file, index=False)
                logging.info("Empty history saved")

        except Exception as e:
            logging.error(f"Failed to save history: {e}")
            raise OperationError(f"Failed to save history: {e}")

    def load_history(self) -> None:
        """Load calculation history from a CSV file using pandas."""
        try:
            if self.config.history_file.exists():
                df = pd.read_csv(self.config.history_file)
                if not df.empty:
                    self.history = [
                        Calculation.from_dict(row.to_dict())
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

    # --------------------
    # History utilities
    # --------------------
    def get_history_dataframe(self) -> pd.DataFrame:
        """Get calculation history as a pandas DataFrame."""
        return pd.DataFrame([calc.to_dict() for calc in self.history])

    def show_history(self) -> List[str]:
        """Get formatted history of calculations."""
        return [
            f"{calc.operation}({calc.operand1}, {calc.operand2}) = {calc.result}"
            for calc in self.history
        ]

    def clear_history(self) -> None:
        """Clear calculation history and undo/redo stacks."""
        self.history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        logging.info("History cleared")

    # --------------------
    # Memento pattern
    # --------------------
    def undo(self) -> bool:
        """Undo the last operation."""
        if not self.undo_stack:
            return False
        memento = self.undo_stack.pop()
        self.redo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True

    def redo(self) -> bool:
        """Redo the previously undone operation."""
        if not self.redo_stack:
            return False
        memento = self.redo_stack.pop()
        self.undo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True
