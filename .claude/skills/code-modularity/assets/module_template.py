"""
Module Template for Modular Code Structure

This template demonstrates how to structure a modular Python module with clear
separation of concerns, well-defined interfaces, and proper documentation.
"""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import logging


# Define interfaces/abstract base classes for loose coupling
class DataProcessorInterface(ABC):
    """Interface for data processing operations."""

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return the result."""
        pass


class ServiceInterface(ABC):
    """Interface for service operations."""

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the service operation with given parameters."""
        pass


# Implementation of a specific data processor
class ExampleDataProcessor(DataProcessorInterface):
    """
    Example implementation of a data processor.

    This class handles data transformation and validation logic.
    It follows the single responsibility principle by focusing only on data processing.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data.

        Args:
            data: Input data to process

        Returns:
            Processed data
        """
        try:
            # Add processing logic here
            processed_data = self._transform_data(data)
            validated_data = self._validate_data(processed_data)
            return validated_data
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            raise

    def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Private method to transform data."""
        # Transformation logic goes here
        return data

    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Private method to validate data."""
        # Validation logic goes here
        return data


# Implementation of a specific service
class ExampleService(ServiceInterface):
    """
    Example implementation of a service.

    This class orchestrates business logic and coordinates with other modules.
    It depends on abstractions rather than concrete implementations.
    """

    def __init__(self, data_processor: DataProcessorInterface):
        """
        Initialize the service with its dependencies.

        Args:
            data_processor: Implementation of DataProcessorInterface
        """
        self.data_processor = data_processor
        self.logger = logging.getLogger(__name__)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the service operation.

        Args:
            params: Parameters for the operation

        Returns:
            Result of the operation
        """
        try:
            # Business logic goes here
            processed_data = self.data_processor.process(params)
            result = self._perform_business_logic(processed_data)
            return result
        except Exception as e:
            self.logger.error(f"Service execution failed: {e}")
            raise

    def _perform_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Private method to perform business logic."""
        # Business logic implementation goes here
        return data


# Public API functions that other modules can use
def create_example_service() -> ServiceInterface:
    """
    Factory function to create an instance of ExampleService.

    This function encapsulates the creation logic and dependency injection,
    making it easier for other modules to use this service without knowing
    the internal implementation details.

    Returns:
        Instance of ExampleService
    """
    data_processor = ExampleDataProcessor()
    return ExampleService(data_processor)


def process_single_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to process a single item.

    This is a simplified API for common use cases that don't require
    the full service interface.

    Args:
        item: Item to process

    Returns:
        Processed item
    """
    service = create_example_service()
    return service.execute(item)


# Module-level constants (if needed)
MODULE_NAME = "example_module"
VERSION = "1.0.0"


# Module initialization (if needed)
def init_module():
    """
    Initialize the module if needed.

    This function can be called when the module is first imported
    to set up any required resources or configurations.
    """
    logging.info(f"Initializing {MODULE_NAME} v{VERSION}")


# If this module is run directly, execute tests or examples
if __name__ == "__main__":
    # Example usage of the module
    print(f"Module {MODULE_NAME} v{VERSION} - Template for modular code")

    # Create and use the service
    service = create_example_service()
    sample_data = {"example": "data", "value": 42}
    result = service.execute(sample_data)
    print(f"Processed result: {result}")