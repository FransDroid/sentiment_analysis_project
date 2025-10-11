import logging
import traceback
from functools import wraps
from typing import Dict, Any
import time

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.last_errors = {}

    def handle_api_error(self, api_name: str, error: Exception) -> Dict[str, Any]:
        """Handle API-related errors with retry logic"""
        error_key = f"{api_name}_{type(error).__name__}"

        # Track error frequency
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = {
            'timestamp': time.time(),
            'error': str(error),
            'traceback': traceback.format_exc()
        }

        self.logger.error(f"API Error in {api_name}: {error}")

        # Determine if we should retry
        should_retry = self._should_retry(error, self.error_counts[error_key])

        return {
            'success': False,
            'error': str(error),
            'api': api_name,
            'should_retry': should_retry,
            'error_count': self.error_counts[error_key]
        }

    def handle_database_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle database-related errors"""
        self.logger.error(f"Database Error in {operation}: {error}")
        self.logger.debug(traceback.format_exc())

        return {
            'success': False,
            'error': str(error),
            'operation': operation,
            'timestamp': time.time()
        }

    def handle_processing_error(self, stage: str, error: Exception, data_context: Dict = None) -> Dict[str, Any]:
        """Handle data processing errors"""
        self.logger.error(f"Processing Error in {stage}: {error}")

        if data_context:
            self.logger.debug(f"Data context: {data_context}")

        return {
            'success': False,
            'error': str(error),
            'stage': stage,
            'data_context': data_context,
            'timestamp': time.time()
        }

    def _should_retry(self, error: Exception, error_count: int) -> bool:
        """Determine if an operation should be retried based on error type and count"""

        # Don't retry after too many failures
        if error_count > 5:
            return False

        # Retry for network-related errors
        if any(term in str(error).lower() for term in ['timeout', 'connection', 'network']):
            return True

        # Retry for rate limiting
        if any(term in str(error).lower() for term in ['rate limit', 'too many requests']):
            return True

        # Don't retry for authentication errors
        if any(term in str(error).lower() for term in ['unauthorized', 'forbidden', 'invalid credentials']):
            return False

        # Default: retry for first few attempts
        return error_count <= 3

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        recent_errors = {}

        for error_key, error_info in self.last_errors.items():
            # Only include errors from last hour
            if time.time() - error_info['timestamp'] < 3600:
                recent_errors[error_key] = {
                    'count': self.error_counts.get(error_key, 0),
                    'last_occurrence': error_info['timestamp'],
                    'error_message': error_info['error']
                }

        return recent_errors

    def reset_error_counts(self):
        """Reset error counters (useful for periodic cleanup)"""
        self.error_counts.clear()
        self.last_errors.clear()

def with_error_handling(error_handler: ErrorHandler, operation_name: str):
    """Decorator to add error handling to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_result = error_handler.handle_processing_error(
                    operation_name, e, {'args': str(args), 'kwargs': str(kwargs)}
                )
                logging.getLogger(func.__module__).error(f"Error in {func.__name__}: {e}")
                return error_result
        return wrapper
    return decorator

# Global error handler instance
error_handler = ErrorHandler()