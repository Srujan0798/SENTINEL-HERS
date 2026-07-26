import os
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class SecretManager:
    """Secure secret management system with encryption and validation."""
    
    def __init__(self):
        self._secrets_cache: dict[str, str] = {}
        self._fernet_key: Optional[bytes] = None
        self._initialized = False
    
    def _generate_fernet_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Generate a Fernet key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _encrypt_value(self, value: str, key: bytes) -> str:
        """Encrypt a value using Fernet encryption."""
        fernet = Fernet(key)
        encrypted = fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt_value(self, encrypted_value: str, key: bytes) -> str:
        """Decrypt a value using Fernet encryption."""
        fernet = Fernet(key)
        encrypted = base64.urlsafe_b64decode(encrypted_value.encode())
        return fernet.decrypt(encrypted).decode()
    
    def initialize(self, master_password: Optional[str] = None) -> None:
        """Initialize the secret manager with environment variables."""
        try:
            # Get master password from environment or generate one
            master_pwd = master_password or os.getenv("SECRET_MASTER_PASSWORD")
            if not master_pwd:
                # Generate a random master password if not provided
                master_pwd = Fernet.generate_key().decode()
                logger.warning("No master password provided, using randomly generated one")
            
            # Get encryption salt from environment
            salt = os.getenv("SECRET_SALT")
            if not salt:
                salt = base64.urlsafe_b64encode(os.urandom(16)).decode()
                os.environ["SECRET_SALT"] = salt
            
            # Generate Fernet key
            self._fernet_key = self._generate_fernet_key(master_pwd, salt.encode())
            self._initialized = True
            logger.info("Secret manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize secret manager: {e}")
            raise
    
    def get_secret(self, key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
        """Get a secret with proper validation and caching."""
        if not self._initialized:
            raise RuntimeError("Secret manager not initialized")
        
        # Check cache first
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        # Get from environment
        value = os.getenv(key)
        
        if value is None:
            if required:
                raise ValueError(f"Required secret '{key}' not found in environment")
            return default
        
        # Validate secret format
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Secret '{key}' is empty or invalid")
        
        # Cache the decrypted value
        self._secrets_cache[key] = value
        return value
    
    def get_encrypted_secret(self, key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
        """Get an encrypted secret and decrypt it."""
        encrypted_value = self.get_secret(key, default, required)
        if encrypted_value is None:
            return None
        
        try:
            return self._decrypt_value(encrypted_value, self._fernet_key)
        except Exception as e:
            logger.error(f"Failed to decrypt secret '{key}': {e}")
            raise
    
    def set_secret(self, key: str, value: str, encrypt: bool = True) -> None:
        """Set a secret with optional encryption."""
        if not self._initialized:
            raise RuntimeError("Secret manager not initialized")
        
        if encrypt and self._fernet_key:
            value = self._encrypt_value(value, self._fernet_key)
        
        os.environ[key] = value
        self._secrets_cache[key] = value
    
    def validate_secrets(self, required_secrets: list[str]) -> dict[str, bool]:
        """Validate that all required secrets are present and valid."""
        results = {}
        for secret in required_secrets:
            try:
                self.get_secret(secret, required=True)
                results[secret] = True
            except Exception as e:
                logger.error(f"Secret validation failed for '{secret}': {e}")
                results[secret] = False
        return results
    
    def rotate_secrets(self, old_master_password: str, new_master_password: str) -> None:
        """Rotate all encrypted secrets with a new master password."""
        if not self._initialized:
            raise RuntimeError("Secret manager not initialized")
        
        # Get current salt
        salt = os.getenv("SECRET_SALT")
        if not salt:
            raise ValueError("Cannot rotate secrets: no salt found")
        
        # Generate new key
        new_key = self._generate_fernet_key(new_master_password, salt.encode())
        
        # Re-encrypt all cached secrets
        for key, value in self._secrets_cache.items():
            if key.startswith(("JWT_", "SECRET_", "API_KEY_")):
                new_value = self._encrypt_value(value, new_key)
                os.environ[key] = new_value
        
        self._fernet_key = new_key
        logger.info("Secrets rotated successfully")

# Global secret manager instance
secret_manager = SecretManager()

def initialize_secrets() -> None:
    """Initialize secrets with proper validation."""
    try:
        secret_manager.initialize()
        
        # Validate critical secrets
        critical_secrets = [
            "JWT_SECRET",
            "JWT_REFRESH_SECRET", 
            "DATABASE_URL",
            "REDIS_URL"
        ]
        
        validation_results = secret_manager.validate_secrets(critical_secrets)
        missing_secrets = [s for s, valid in validation_results.items() if not valid]
        
        if missing_secrets:
            raise ValueError(f"Missing critical secrets: {missing_secrets}")
        
        logger.info("All critical secrets validated successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize secrets: {e}")
        raise

def get_jwt_secret() -> str:
    """Get JWT secret with proper validation."""
    return secret_manager.get_secret("JWT_SECRET", required=True)

def get_jwt_refresh_secret() -> str:
    """Get JWT refresh secret with proper validation."""
    return secret_manager.get_secret("JWT_REFRESH_SECRET", required=True)

def get_database_url() -> str:
    """Get database URL with proper validation."""
    return secret_manager.get_secret("DATABASE_URL", required=True)

def get_redis_url() -> str:
    """Get Redis URL with proper validation."""
    return secret_manager.get_secret("REDIS_URL", required=True)

# Initialize secrets when module is imported
try:
    initialize_secrets()
except Exception as e:
    logger.warning(f"Secret initialization failed: {e}. Running with limited functionality.")