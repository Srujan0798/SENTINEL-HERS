"""Test configuration for missing secrets."""

import os
from dotenv import load_dotenv

# Load test environment
load_dotenv()

# Set test secrets
os.environ['JWT_SECRET'] = 'test-secret-key-for-jwt-token-generation'
os.environ['JWT_REFRESH_SECRET'] = 'test-refresh-secret-key-for-jwt-token-generation'
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['AI_SERVICE_API_KEY'] = 'test-api-key-for-ai-service'
os.environ['AI_SERVICE_URL'] = 'http://localhost:8001'

# Create test database URL if not exists
if not os.path.exists('test.db'):
    open('test.db', 'w').close()