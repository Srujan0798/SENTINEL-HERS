import os
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time

class SecurityHeadersMiddleware:
    """Add security headers to all responses."""
    
    def __init__(self, app: Callable):
        self.app = app
    
    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add security headers
                headers = dict(message.get("headers", []))
                
                # Content Security Policy
                headers[b"content-security-policy"] = self._get_csp_header()
                
                # Strict Transport Security (HTTPS only in production)
                if os.getenv("ENV", "development").lower() == "production":
                    headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains; preload"
                
                # Other security headers
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-frame-options"] = b"DENY"
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                headers[b"permissions-policy"] = self._get_permissions_policy()
                
                # Remove potentially dangerous headers
                dangerous_headers = [
                    b"server",
                    b"x-powered-by",
                ]
                for header in dangerous_headers:
                    headers.pop(header, None)
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, send_wrapper)
    
    def _get_csp_header(self) -> bytes:
        """Generate Content Security Policy header."""
        csp = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "connect-src 'self' https:",
            "font-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        return "; ".join(csp).encode()
    
    def _get_permissions_policy(self) -> bytes:
        """Generate Permissions Policy header."""
        policy = [
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=()",
            "battery=()",
            "bluetooth=()",
            "browsing-topics=()",
            "camera=()",
            "cross-origin-isolated=()",
            "display-capture=()",
            "document-domain=()",
            "encrypted-media=()",
            "execution-while-not-rendered=()",
            "execution-while-out-of-viewport=()",
            "fullscreen=()",
            "geolocation=()",
            "gyroscope=()",
            "hid=()",
            "identity-credentials-get=()",
            "local-fonts=()",
            "magnetometer=()",
            "microphone=()",
            "midi=()",
            "navigation-override=()",
            "payment=()",
            "picture-in-picture=()",
            "publickey-credentials-get=()",
            "screen-wake-lock=()",
            "serial=()",
            "storage-access=()",
            "sync-xhr=()",
            "usb=()",
            "web-share=()",
            "window-management=()",
            "xr-spatial-tracking=()",
        ]
        return ", ".join(policy).encode()

class RateLimitMiddleware:
    """Simple rate limiting middleware."""
    
    def __init__(self, app: Callable, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        client_ip = scope["client"][0]
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_seconds
            ]
        
        # Check rate limit
        if client_ip in self.requests and len(self.requests[client_ip]) >= self.max_requests:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "retry-after": str(self.window_seconds),
                    "x-ratelimit-limit": str(self.max_requests),
                    "x-ratelimit-remaining": "0",
                    "x-ratelimit-reset": str(int(current_time + self.window_seconds)),
                }
            )
            await response(scope, receive, send)
            return
        
        # Record request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        # Add rate limit headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                remaining = max(0, self.max_requests - len(self.requests[client_ip]))
                reset_time = int(current_time + self.window_seconds)
                
                headers[b"x-ratelimit-limit"] = str(self.max_requests).encode()
                headers[b"x-ratelimit-remaining"] = str(remaining).encode()
                headers[b"x-ratelimit-reset"] = str(reset_time).encode()
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, send_wrapper)