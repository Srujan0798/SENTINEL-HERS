import time
import asyncio
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union, List
from datetime import datetime, timedelta
import logging
import threading
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class CircuitMetrics:
    """Metrics for circuit breaker monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    average_response_time: float = 0.0
    slow_calls_count: int = 0

class AdvancedCircuitBreaker:
    """Advanced circuit breaker with monitoring and adaptive thresholds."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        timeout: int = 30,
        slow_call_threshold: float = 1.0,
        adaptive_threshold: bool = True,
        health_check_interval: int = 300
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.timeout = timeout
        self.slow_call_threshold = slow_call_threshold
        self.adaptive_threshold = adaptive_threshold
        self.health_check_interval = health_check_interval
        
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.lock = threading.Lock()
        
        # Adaptive threshold adjustment
        self.base_failure_threshold = failure_threshold
        self.current_failure_threshold = failure_threshold
        
        # Health check
        self.last_health_check = None
        self.health_check_task = None
        
        # Callbacks
        self.success_callback = None
        self.failure_callback = None
        self.state_change_callback = None
        
        # Start health check task
        self._start_health_check()
    
    def _start_health_check(self):
        """Start background health check task."""
        if self.health_check_task:
            return
        
        def health_check_loop():
            while True:
                try:
                    self._perform_health_check()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health check failed for {self.name}: {e}")
                    time.sleep(self.health_check_interval)
        
        self.health_check_task = threading.Thread(target=health_check_loop, daemon=True)
        self.health_check_task.start()
    
    def _perform_health_check(self):
        """Perform health check for the service."""
        # This can be overridden by subclasses for specific service health checks
        pass
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.state != CircuitState.OPEN:
            return False
        
        if self.metrics.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.metrics.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def _update_metrics(self, success: bool, response_time: float):
        """Update circuit breaker metrics."""
        with self.lock:
            self.metrics.total_calls += 1
            
            if success:
                self.metrics.successful_calls += 1
                self.metrics.consecutive_failures = 0
                self.metrics.last_success_time = datetime.now()
                
                # Update average response time
                if self.metrics.total_calls > 1:
                    self.metrics.average_response_time = (
                        (self.metrics.average_response_time * (self.metrics.total_calls - 1) + response_time) 
                        / self.metrics.total_calls
                    )
                else:
                    self.metrics.average_response_time = response_time
                
                # Check for slow calls
                if response_time > self.slow_call_threshold:
                    self.metrics.slow_calls_count += 1
            else:
                self.metrics.failed_calls += 1
                self.metrics.consecutive_failures += 1
                self.metrics.last_failure_time = datetime.now()
                
                # Adaptive threshold adjustment
                if self.adaptive_threshold and self.metrics.total_calls > 10:
                    failure_rate = self.metrics.failed_calls / self.metrics.total_calls
                    if failure_rate > 0.5:  # 50% failure rate
                        self.current_failure_threshold = min(
                            self.base_failure_threshold + 2,
                            self.base_failure_threshold * 2
                        )
                    else:
                        self.current_failure_threshold = max(
                            self.base_failure_threshold - 1,
                            self.base_failure_threshold
                        )
    
    def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            logger.info(f"Circuit breaker '{self.name}' state changed: {old_state} -> {new_state}")
            
            if self.state_change_callback:
                self.state_change_callback(old_state, new_state)
    
    def _on_success(self, response_time: float):
        """Handle successful call."""
        self._update_metrics(True, response_time)
        
        if self.state == CircuitState.HALF_OPEN:
            self._change_state(CircuitState.CLOSED)
            logger.info(f"Circuit breaker '{self.name}' reset to CLOSED after successful call")
        
        if self.success_callback:
            self.success_callback(self.metrics)
    
    def _on_failure(self, response_time: float):
        """Handle failed call."""
        self._update_metrics(False, response_time)
        
        if self.state == CircuitState.CLOSED:
            if self.metrics.consecutive_failures >= self.current_failure_threshold:
                self._change_state(CircuitState.OPEN)
                logger.warning(f"Circuit breaker '{self.name}' OPEN after {self.metrics.consecutive_failures} failures")
        
        if self.failure_callback:
            self.failure_callback(self.metrics)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._change_state(CircuitState.HALF_OPEN)
                    logger.info(f"Circuit breaker '{self.name}' attempting reset")
                else:
                    raise Exception(f"Circuit breaker '{self.name}' is OPEN")
            
            try:
                # Set timeout for the call
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                
                self._on_success(response_time)
                return result
                
            except self.expected_exception as e:
                response_time = time.time() - start_time
                self._on_failure(response_time)
                raise e
            
            except Exception as e:
                response_time = time.time() - start_time
                self._on_failure(response_time)
                raise e
        
        return wrapper
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state
    
    def get_metrics(self) -> CircuitMetrics:
        """Get current circuit breaker metrics."""
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        with self.lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "metrics": {
                    "total_calls": self.metrics.total_calls,
                    "successful_calls": self.metrics.successful_calls,
                    "failed_calls": self.metrics.failed_calls,
                    "success_rate": self.metrics.successful_calls / max(self.metrics.total_calls, 1),
                    "consecutive_failures": self.metrics.consecutive_failures,
                    "average_response_time": self.metrics.average_response_time,
                    "slow_calls_count": self.metrics.slow_calls_count
                },
                "thresholds": {
                    "failure_threshold": self.current_failure_threshold,
                    "recovery_timeout": self.recovery_timeout,
                    "timeout": self.timeout,
                    "slow_call_threshold": self.slow_call_threshold
                }
            }
    
    def reset(self):
        """Reset the circuit breaker."""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitMetrics()
            self.current_failure_threshold = self.base_failure_threshold
            logger.info(f"Circuit breaker '{self.name}' reset")
    
    def set_success_callback(self, callback: Callable):
        """Set callback for successful calls."""
        self.success_callback = callback
    
    def set_failure_callback(self, callback: Callable):
        """Set callback for failed calls."""
        self.failure_callback = callback
    
    def set_state_change_callback(self, callback: Callable):
        """Set callback for state changes."""
        self.state_change_callback = callback

# Global circuit breakers for different services
ai_circuit_breaker = AdvancedCircuitBreaker(
    name="ai_service",
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception,
    timeout=30,
    slow_call_threshold=2.0
)

database_circuit_breaker = AdvancedCircuitBreaker(
    name="database",
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
    timeout=10,
    slow_call_threshold=1.0
)

external_service_circuit_breaker = AdvancedCircuitBreaker(
    name="external_service",
    failure_threshold=3,
    recovery_timeout=45,
    expected_exception=Exception,
    timeout=20,
    slow_call_threshold=3.0
)

def circuit_breaker(service_type: str = "default") -> AdvancedCircuitBreaker:
    """Get circuit breaker for specific service type."""
    if service_type == "ai":
        return ai_circuit_breaker
    elif service_type == "database":
        return database_circuit_breaker
    elif service_type == "external":
        return external_service_circuit_breaker
    else:
        return external_service_circuit_breaker

def with_circuit_breaker(service_type: str = "default"):
    """Decorator to apply circuit breaker to a function."""
    def decorator(func: Callable) -> Callable:
        cb = circuit_breaker(service_type)
        return cb(func)
    return decorator

class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""
    
    def __init__(self):
        self.breakers: Dict[str, AdvancedCircuitBreaker] = {}
    
    def add_breaker(self, name: str, breaker: AdvancedCircuitBreaker):
        """Add a circuit breaker."""
        self.breakers[name] = breaker
    
    def get_breaker(self, name: str) -> Optional[AdvancedCircuitBreaker]:
        """Get a circuit breaker by name."""
        return self.breakers.get(name)
    
    def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all circuit breakers."""
        return {
            name: breaker.get_health_status()
            for name, breaker in self.breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            breaker.reset()

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Initialize with default breakers
circuit_breaker_manager.add_breaker("ai", ai_circuit_breaker)
circuit_breaker_manager.add_breaker("database", database_circuit_breaker)
circuit_breaker_manager.add_breaker("external", external_service_circuit_breaker)