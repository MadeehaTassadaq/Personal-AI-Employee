"""Error recovery service with retry logic and graceful degradation."""

import asyncio
import functools
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, TypeVar
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ServiceHealth:
    """Tracks health of a service."""
    name: str
    status: ServiceStatus = ServiceStatus.HEALTHY
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0
    circuit_open_until: Optional[datetime] = None


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class ErrorRecoveryService:
    """Manages error recovery, retries, and service health."""

    def __init__(self):
        self._services: dict[str, ServiceHealth] = {}
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_reset_time = timedelta(minutes=5)
        self._degradation_callbacks: list[Callable[[str, ServiceStatus], None]] = []

    def register_service(self, name: str) -> None:
        """Register a service for health tracking."""
        if name not in self._services:
            self._services[name] = ServiceHealth(name=name)
            logger.info(f"Registered service: {name}")

    def get_service_health(self, name: str) -> Optional[ServiceHealth]:
        """Get health status of a service."""
        return self._services.get(name)

    def get_all_health(self) -> dict[str, ServiceHealth]:
        """Get health status of all services."""
        return self._services.copy()

    def record_success(self, service_name: str) -> None:
        """Record a successful operation for a service."""
        if service_name not in self._services:
            self.register_service(service_name)

        service = self._services[service_name]
        service.last_success = datetime.now()
        service.success_count += 1
        service.consecutive_failures = 0

        # Recover from degraded state
        if service.status != ServiceStatus.HEALTHY:
            old_status = service.status
            service.status = ServiceStatus.HEALTHY
            service.circuit_open_until = None
            self._notify_status_change(service_name, old_status, ServiceStatus.HEALTHY)

    def record_failure(self, service_name: str, error: Optional[Exception] = None) -> None:
        """Record a failed operation for a service."""
        if service_name not in self._services:
            self.register_service(service_name)

        service = self._services[service_name]
        service.last_failure = datetime.now()
        service.failure_count += 1
        service.consecutive_failures += 1

        # Check for circuit breaker
        if service.consecutive_failures >= self._circuit_breaker_threshold:
            old_status = service.status
            service.status = ServiceStatus.UNHEALTHY
            service.circuit_open_until = datetime.now() + self._circuit_breaker_reset_time
            if old_status != ServiceStatus.UNHEALTHY:
                self._notify_status_change(service_name, old_status, ServiceStatus.UNHEALTHY)
                logger.warning(
                    f"Circuit breaker opened for {service_name}. "
                    f"Will reset at {service.circuit_open_until}"
                )
        elif service.consecutive_failures >= 2:
            old_status = service.status
            if old_status != ServiceStatus.DEGRADED:
                service.status = ServiceStatus.DEGRADED
                self._notify_status_change(service_name, old_status, ServiceStatus.DEGRADED)

    def is_circuit_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for a service."""
        service = self._services.get(service_name)
        if not service or not service.circuit_open_until:
            return False

        if datetime.now() >= service.circuit_open_until:
            # Reset circuit breaker (half-open state)
            service.circuit_open_until = None
            service.status = ServiceStatus.DEGRADED
            return False

        return True

    def on_status_change(self, callback: Callable[[str, ServiceStatus], None]) -> None:
        """Register a callback for service status changes."""
        self._degradation_callbacks.append(callback)

    def _notify_status_change(
        self, service_name: str, old_status: ServiceStatus, new_status: ServiceStatus
    ) -> None:
        """Notify callbacks of status change."""
        logger.info(f"Service {service_name} status changed: {old_status} -> {new_status}")
        for callback in self._degradation_callbacks:
            try:
                callback(service_name, new_status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")


def calculate_backoff(
    attempt: int,
    config: RetryConfig = RetryConfig()
) -> float:
    """Calculate exponential backoff delay with optional jitter."""
    import random

    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)

    if config.jitter:
        delay = delay * (0.5 + random.random())

    return delay


def with_retry(
    config: Optional[RetryConfig] = None,
    service_name: Optional[str] = None,
    recovery_service: Optional[ErrorRecoveryService] = None
):
    """Decorator for retrying functions with exponential backoff.

    Args:
        config: Retry configuration
        service_name: Name of service for health tracking
        recovery_service: Error recovery service instance
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None

            # Check circuit breaker
            if recovery_service and service_name and recovery_service.is_circuit_open(service_name):
                raise CircuitBreakerOpenError(f"Circuit breaker open for {service_name}")

            for attempt in range(config.max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if recovery_service and service_name:
                        recovery_service.record_success(service_name)
                    return result

                except Exception as e:
                    last_exception = e
                    if recovery_service and service_name:
                        recovery_service.record_failure(service_name, e)

                    if attempt < config.max_retries:
                        delay = calculate_backoff(attempt, config)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            import time
            last_exception = None

            if recovery_service and service_name and recovery_service.is_circuit_open(service_name):
                raise CircuitBreakerOpenError(f"Circuit breaker open for {service_name}")

            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if recovery_service and service_name:
                        recovery_service.record_success(service_name)
                    return result

                except Exception as e:
                    last_exception = e
                    if recovery_service and service_name:
                        recovery_service.record_failure(service_name, e)

                    if attempt < config.max_retries:
                        delay = calculate_backoff(attempt, config)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Platform-specific error types and handlers
class PlatformError(Exception):
    """Base class for platform-specific errors."""
    platform: str = "unknown"
    recoverable: bool = True
    retry_after: Optional[float] = None


class RateLimitError(PlatformError):
    """Rate limit exceeded."""
    def __init__(self, platform: str, retry_after: Optional[float] = None):
        self.platform = platform
        self.retry_after = retry_after or 60.0
        super().__init__(f"{platform} rate limit exceeded. Retry after {self.retry_after}s")


class AuthenticationError(PlatformError):
    """Authentication/token error."""
    recoverable = False
    def __init__(self, platform: str, message: str = ""):
        self.platform = platform
        super().__init__(f"{platform} authentication failed: {message}")


class APIError(PlatformError):
    """Generic API error."""
    def __init__(self, platform: str, status_code: int, message: str = ""):
        self.platform = platform
        self.status_code = status_code
        self.recoverable = status_code >= 500  # Server errors are recoverable
        super().__init__(f"{platform} API error ({status_code}): {message}")


@dataclass
class GracefulDegradationResult:
    """Result of graceful degradation check."""
    can_proceed: bool
    available_platforms: list[str]
    failed_platforms: list[str]
    fallback_action: Optional[str] = None
    message: str = ""


class PlatformRecoveryHandler:
    """Handles platform-specific error recovery."""

    # Platform-specific retry configurations
    PLATFORM_CONFIGS = {
        "gmail": RetryConfig(max_retries=3, base_delay=2.0),
        "linkedin": RetryConfig(max_retries=2, base_delay=5.0),
        "facebook": RetryConfig(max_retries=3, base_delay=3.0),
        "instagram": RetryConfig(max_retries=3, base_delay=3.0),
        "twitter": RetryConfig(max_retries=2, base_delay=1.0),
        "odoo": RetryConfig(max_retries=5, base_delay=1.0),
        "whatsapp": RetryConfig(max_retries=3, base_delay=2.0),
    }

    # Platform groups for fallback strategies
    PLATFORM_GROUPS = {
        "social": ["linkedin", "facebook", "instagram", "twitter"],
        "messaging": ["whatsapp", "gmail"],
        "accounting": ["odoo"],
    }

    def __init__(self, recovery_service: "ErrorRecoveryService"):
        self.recovery_service = recovery_service

    def get_retry_config(self, platform: str) -> RetryConfig:
        """Get platform-specific retry configuration."""
        return self.PLATFORM_CONFIGS.get(platform, RetryConfig())

    async def handle_platform_error(
        self,
        platform: str,
        error: Exception
    ) -> tuple[bool, Optional[str]]:
        """Handle a platform-specific error.

        Args:
            platform: Platform name
            error: The exception that occurred

        Returns:
            Tuple of (should_retry, fallback_action)
        """
        self.recovery_service.record_failure(platform, error)

        if isinstance(error, RateLimitError):
            logger.warning(f"Rate limited on {platform}. Waiting {error.retry_after}s")
            return True, None

        if isinstance(error, AuthenticationError):
            logger.error(f"Auth error on {platform}. Needs manual intervention.")
            return False, f"refresh_{platform}_token"

        if isinstance(error, APIError):
            if error.recoverable:
                return True, None
            return False, f"check_{platform}_api_status"

        # Unknown error - check service health
        health = self.recovery_service.get_service_health(platform)
        if health and health.status == ServiceStatus.UNHEALTHY:
            return False, f"circuit_breaker_open_for_{platform}"

        return True, None

    def graceful_degradation(
        self,
        failed_platforms: list[str],
        required_platforms: Optional[list[str]] = None
    ) -> GracefulDegradationResult:
        """Determine if operation can continue with available platforms.

        Args:
            failed_platforms: List of platforms that failed
            required_platforms: Platforms required for operation (optional)

        Returns:
            GracefulDegradationResult with available options
        """
        all_platforms = set()
        for group in self.PLATFORM_GROUPS.values():
            all_platforms.update(group)

        available = [p for p in all_platforms if p not in failed_platforms]

        # Check health of available platforms
        healthy_available = []
        for platform in available:
            health = self.recovery_service.get_service_health(platform)
            if not health or health.status != ServiceStatus.UNHEALTHY:
                healthy_available.append(platform)

        # If required platforms specified, check if any are available
        if required_platforms:
            required_available = [p for p in required_platforms if p in healthy_available]
            if not required_available:
                return GracefulDegradationResult(
                    can_proceed=False,
                    available_platforms=healthy_available,
                    failed_platforms=failed_platforms,
                    message=f"None of required platforms available: {required_platforms}"
                )

        # Determine fallback action based on what failed
        fallback = None
        if "gmail" in failed_platforms and "whatsapp" in healthy_available:
            fallback = "use_whatsapp_instead"
        elif "whatsapp" in failed_platforms and "gmail" in healthy_available:
            fallback = "use_gmail_instead"

        # For social platforms, can continue with partial posting
        social_failed = [p for p in failed_platforms if p in self.PLATFORM_GROUPS["social"]]
        social_available = [p for p in healthy_available if p in self.PLATFORM_GROUPS["social"]]

        if social_failed and social_available:
            fallback = f"partial_social_post_to_{','.join(social_available)}"

        return GracefulDegradationResult(
            can_proceed=len(healthy_available) > 0,
            available_platforms=healthy_available,
            failed_platforms=failed_platforms,
            fallback_action=fallback,
            message=f"Operating with {len(healthy_available)}/{len(all_platforms)} platforms"
        )

    def get_health_report(self) -> dict:
        """Get a health report for all platforms."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "platforms": {},
            "summary": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0
            }
        }

        for platform, config in self.PLATFORM_CONFIGS.items():
            health = self.recovery_service.get_service_health(platform)
            if health:
                status = health.status.value
                report["platforms"][platform] = {
                    "status": status,
                    "consecutive_failures": health.consecutive_failures,
                    "last_success": health.last_success.isoformat() if health.last_success else None,
                    "last_failure": health.last_failure.isoformat() if health.last_failure else None,
                    "circuit_open_until": health.circuit_open_until.isoformat() if health.circuit_open_until else None
                }
                report["summary"][status] += 1
            else:
                report["platforms"][platform] = {"status": "unknown"}

        return report


# Global error recovery service instance
_error_recovery: Optional[ErrorRecoveryService] = None
_platform_handler: Optional[PlatformRecoveryHandler] = None


def get_error_recovery() -> ErrorRecoveryService:
    """Get or create the global error recovery service."""
    global _error_recovery
    if _error_recovery is None:
        _error_recovery = ErrorRecoveryService()
        # Register all services including new Gold Tier platforms
        for service in [
            "gmail", "whatsapp", "linkedin", "file_watcher", "orchestrator",
            "facebook", "instagram", "twitter", "odoo"
        ]:
            _error_recovery.register_service(service)
    return _error_recovery


def get_platform_handler() -> PlatformRecoveryHandler:
    """Get or create the platform recovery handler."""
    global _platform_handler
    if _platform_handler is None:
        _platform_handler = PlatformRecoveryHandler(get_error_recovery())
    return _platform_handler
