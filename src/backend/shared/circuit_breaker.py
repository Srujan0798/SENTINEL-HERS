"""Advanced circuit breaker implementation with monitoring and health checks."""

import time
import threading
from enum import Enum
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 3
    reset_timeout: int = 30  # seconds
    monitoring_period: int = 60  # seconds
    expected_exception: tuple = (Exception,)
    
    def __post_init__(self):
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.reset_timeout < 1:
            raise ValueError("reset_timeout must be >= 1")
        if self.monitoring_period < 1:
            raise ValueError("monitoring_period must be >= 1")

@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100

class CircuitBreaker:
    """Advanced circuit breaker with monitoring and health checks."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.next_attempt = 0
        self.metrics = CircuitBreakerMetrics()
        self.lock = threading.Lock()
        self._monitoring_thread = None
        self._stop_monitoring = False
        
        # Start monitoring thread
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start the monitoring thread."""
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._stop_monitoring = False
            self._monitoring_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self._monitoring_thread.start()
    
    def _monitor_loop(self):
        """Monitoring loop for health checks."""
        while not self._stop_monitoring:
            time.sleep(self.config.monitoring_period)
            self._perform_health_check()
    
    def _perform_health_check(self):
        """Perform periodic health check."""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                # Check if we should attempt to reset
                current_time = time.time()
                if current_time >= self.next_attempt:
                    logger.info(f"[CircuitBreaker] {self.name}: Health check - attempting reset")
                    self.state = CircuitBreakerState.HALF_OPEN
    
    def execute(self, operation: Callable[[], Any]) -> Any:
        """Execute operation with circuit breaker protection."""
        with self.lock:
            current_time = time.time()
            
            # Check if circuit should be opened
            if self.state == CircuitBreakerState.OPEN:
                if current_time < self.next_attempt:
                    raise Exception(f"{self.name} circuit is OPEN (failure threshold reached)")
                else:
                    # Time to attempt reset
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"[CircuitBreaker] {self.name}: Moving to HALF_OPEN state")
            
            # Execute operation
            try:
                result = operation()
                
                # On success, reset state
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self._on_success()
                
                self.metrics.successful_calls += 1
                self.metrics.total_calls += 1
                self.metrics.last_success_time = datetime.now(timezone.utc)
                
                return result
                
            except Exception as error:
                self._on_failure(error)
                raise error
    
    def _on_success(self):
        """Handle successful operation."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.metrics.consecutive_failures = 0
        logger.info(f"[CircuitBreaker] {self.name}: Circuit CLOSED after successful attempt")
    
    def _on_failure(self, error: Exception):
        """Handle failed operation."""
        self.failure_count += 1
        self.metrics.failed_calls += 1
        self.metrics.total_calls += 1
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = datetime.now(timezone.utc)
        self.metrics.consecutive_failures += 1
        
        # Check if circuit should be opened
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.next_attempt = time.time() + self.config.reset_timeout
            logger.warning(
                f"[CircuitBreaker] {self.name}: Circuit OPEN after {self.failure_count} failures. "
                f"Next attempt in {self.config.reset_timeout}s"
            )
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        with self.lock:
            return self.state
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics."""
        with self.lock:
            return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status including metrics."""
        with self.lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "metrics": {
                    "total_calls": self.metrics.total_calls,
                    "successful_calls": self.metrics.successful_calls,
                    "failed_calls": self.metrics.failed_calls,
                    "success_rate": self.metrics.success_rate,
                    "failure_rate": self.metrics.failure_rate,
                    "consecutive_failures": self.metrics.consecutive_failures,
                    "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                    "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                },
                "thresholds": {
                    "failure_threshold": self.config.failure_threshold,
                    "reset_timeout": self.config.reset_timeout,
                    "monitoring_period": self.config.monitoring_period,
                }
            }
    
    def reset(self):
        """Manually reset the circuit breaker."""
        with self.lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.next_attempt = 0
            self.metrics = CircuitBreakerMetrics()
            logger.info(f"[CircuitBreaker] {self.name}: Circuit manually reset")
    
    def stop(self):
        """Stop the monitoring thread."""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join()

class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.Lock()
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        with self.lock:
            if name not in self.breakers:
                if config is None:
                    config = CircuitBreakerConfig()
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]
    
    def get_all_breakers(self) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers."""
        with self.lock:
            return self.breakers.copy()
    
    def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all circuit breakers."""
        with self.lock:
            return {
                name: breaker.get_health_status()
                for name, breaker in self.breakers.items()
            }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def stop_all(self):
        """Stop all circuit breakers."""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.stop()
            self.breakers.clear()

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Decorator for automatic circuit breaker wrapping
def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to wrap functions with circuit breaker protection."""
    def decorator(func: Callable) -> Callable:
        breaker = circuit_breaker_manager.get_breaker(name, config)
        
        def wrapper(*args, **kwargs):
            return breaker.execute(lambda: func(*args, **kwargs))
        
        # Add breaker methods to wrapper for access
        wrapper.get_breaker = lambda: breaker
        wrapper.get_state = lambda: breaker.get_state()
        wrapper.get_metrics = lambda: breaker.get_metrics()
        wrapper.get_health_status = lambda: breaker.get_health_status()
        wrapper.reset = lambda: breaker.reset()
        
        return wrapper
    return decorator