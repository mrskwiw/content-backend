"""Service for managing user settings and encrypted API keys"""

import os
from typing import Optional
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from ..models.setting import Setting

# Get encryption key from environment or generate one
# In production, this should be stored securely (e.g., AWS Secrets Manager)
ENCRYPTION_KEY = os.getenv("SETTINGS_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key for development (WARNING: This will change on restart!)
    ENCRYPTION_KEY = Fernet.generate_key().decode()

cipher_suite = Fernet(
    ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
)


def encrypt_value(value: str) -> str:
    """Encrypt a sensitive value"""
    if not value:
        return value
    return cipher_suite.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a sensitive value"""
    if not encrypted_value:
        return encrypted_value
    try:
        return cipher_suite.decrypt(encrypted_value.encode()).decode()
    except Exception:
        # If decryption fails, return empty string
        return ""


def get_setting(
    db: Session, user_id: int, key: str, category: str = "integrations", decrypt: bool = True
) -> Optional[str]:
    """
    Get a setting value for a user.

    Args:
        db: Database session
        user_id: User ID
        key: Setting key (e.g., "brave_api_key")
        category: Setting category (e.g., "integrations")
        decrypt: Whether to decrypt the value if encrypted

    Returns:
        Setting value or None if not found
    """
    setting = (
        db.query(Setting)
        .filter(Setting.user_id == user_id, Setting.key == key, Setting.category == category)
        .first()
    )

    if not setting:
        return None

    if setting.is_encrypted and decrypt:
        return decrypt_value(setting.value)

    return setting.value


def set_setting(
    db: Session,
    user_id: int,
    key: str,
    value: Optional[str],
    category: str = "integrations",
    encrypt: bool = True,
) -> Setting:
    """
    Set a setting value for a user.

    Args:
        db: Database session
        user_id: User ID
        key: Setting key (e.g., "brave_api_key")
        value: Setting value
        category: Setting category (e.g., "integrations")
        encrypt: Whether to encrypt the value

    Returns:
        Updated or created Setting object
    """
    # Find existing setting
    setting = (
        db.query(Setting)
        .filter(Setting.user_id == user_id, Setting.key == key, Setting.category == category)
        .first()
    )

    # Encrypt value if requested
    stored_value = encrypt_value(value) if encrypt and value else value

    if setting:
        # Update existing
        setting.value = stored_value
        setting.is_encrypted = 1 if encrypt else 0
    else:
        # Create new
        setting = Setting(
            user_id=user_id,
            key=key,
            value=stored_value,
            category=category,
            is_encrypted=1 if encrypt else 0,
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting


def delete_setting(db: Session, user_id: int, key: str, category: str = "integrations") -> bool:
    """
    Delete a setting for a user.

    Args:
        db: Database session
        user_id: User ID
        key: Setting key
        category: Setting category

    Returns:
        True if deleted, False if not found
    """
    setting = (
        db.query(Setting)
        .filter(Setting.user_id == user_id, Setting.key == key, Setting.category == category)
        .first()
    )

    if setting:
        db.delete(setting)
        db.commit()
        return True

    return False


def get_web_search_config(db: Session, user_id: int) -> dict:
    """
    Get web search configuration for a user.

    Returns:
        dict with keys: provider, brave_api_key, tavily_api_key
    """
    provider = get_setting(db, user_id, "web_search_provider", decrypt=False) or "stub"
    brave_key = get_setting(db, user_id, "brave_api_key") or ""
    tavily_key = get_setting(db, user_id, "tavily_api_key") or ""

    return {
        "provider": provider,
        "brave_api_key": brave_key,
        "tavily_api_key": tavily_key,
    }


def set_web_search_config(
    db: Session,
    user_id: int,
    provider: str,
    brave_api_key: Optional[str] = None,
    tavily_api_key: Optional[str] = None,
) -> dict:
    """
    Set web search configuration for a user.

    Args:
        db: Database session
        user_id: User ID
        provider: "brave", "tavily", or "stub"
        brave_api_key: Brave Search API key (optional)
        tavily_api_key: Tavily API key (optional)

    Returns:
        Updated configuration dict
    """
    # Set provider
    set_setting(db, user_id, "web_search_provider", provider, encrypt=False)

    # Set API keys if provided
    if brave_api_key is not None:
        if brave_api_key:
            set_setting(db, user_id, "brave_api_key", brave_api_key, encrypt=True)
        else:
            delete_setting(db, user_id, "brave_api_key")

    if tavily_api_key is not None:
        if tavily_api_key:
            set_setting(db, user_id, "tavily_api_key", tavily_api_key, encrypt=True)
        else:
            delete_setting(db, user_id, "tavily_api_key")

    return get_web_search_config(db, user_id)
