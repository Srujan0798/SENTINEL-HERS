import { AIProviderError } from "./provider";

export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  monitoringPeriod: number;
}

export class CircuitBreaker {
  private failureCount = 0;
  private lastFailureTime = 0;
  private state: "CLOSED" | "OPEN" | "HALF_OPEN" = "CLOSED";
  private nextAttempt = 0;

  constructor(
    private config: CircuitBreakerConfig,
    private name: string
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    const now = Date.now();

    // Reset circuit breaker if enough time has passed
    if (this.state === "OPEN" && now > this.nextAttempt) {
      this.state = "HALF_OPEN";
      console.log(`[CircuitBreaker] ${this.name}: Moving to HALF_OPEN state`);
    }

    // Check if circuit should be opened
    if (this.state === "OPEN") {
      throw new AIProviderError(
        `${this.name} circuit is OPEN (failure threshold reached)`
      );
    }

    try {
      const result = await operation();
      
      // On success, reset state
      if (this.state === "HALF_OPEN") {
        this.state = "CLOSED";
        this.failureCount = 0;
        console.log(`[CircuitBreaker] ${this.name}: Circuit CLOSED after successful attempt`);
      }
      
      return result;
    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = now;

      if (this.failureCount >= this.config.failureThreshold) {
        this.state = "OPEN";
        this.nextAttempt = now + this.config.resetTimeout;
        console.log(
          `[CircuitBreaker] ${this.name}: Circuit OPEN after ${this.failureCount} failures. Next attempt in ${this.config.resetTimeout/1000}s`
        );
      }

      throw error;
    }
  }

  getState(): "CLOSED" | "OPEN" | "HALF_OPEN" {
    return this.state;
  }

  getFailureCount(): number {
    return this.failureCount;
  }

  reset(): void {
    this.state = "CLOSED";
    this.failureCount = 0;
    this.lastFailureTime = 0;
    this.nextAttempt = 0;
    console.log(`[CircuitBreaker] ${this.name}: Circuit manually reset`);
  }
}

// Pre-configured circuit breakers for different services
export const CIRCUIT_BREAKERS = {
  ai: new CircuitBreaker({
    failureThreshold: 3,
    resetTimeout: 30000, // 30 seconds
    monitoringPeriod: 60000, // 1 minute
  }, "AI Service"),
  
  database: new CircuitBreaker({
    failureThreshold: 5,
    resetTimeout: 10000, // 10 seconds
    monitoringPeriod: 30000, // 30 seconds
  }, "Database"),
  
  external: new CircuitBreaker({
    failureThreshold: 2,
    resetTimeout: 60000, // 1 minute
    monitoringPeriod: 120000, // 2 minutes
  }, "External API"),
};

// Decorator for automatic circuit breaker wrapping
export function withCircuitBreaker<T extends any[], R>(
  breaker: CircuitBreaker,
  fn: (...args: T) => Promise<R>
) {
  return (...args: T): Promise<R> => {
    return breaker.execute(() => fn(...args));
  };
}