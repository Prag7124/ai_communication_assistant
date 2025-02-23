import os
import logging
from pathlib import Path
from dotenv import load_dotenv

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Handles application configuration by loading environment variables."""

    REQUIRED_VARS = {
        "GMAIL_CLIENT_ID": "OAuth Client ID for Gmail API",
        "GMAIL_CLIENT_SECRET": "OAuth Client Secret for Gmail API",
        "GMAIL_REFRESH_TOKEN": "OAuth Refresh Token for Gmail API",
        "TWILIO_ACCOUNT_SID": "Twilio API Account SID",
        "TWILIO_AUTH_TOKEN": "Twilio API Auth Token",
        "SLACK_BOT_TOKEN": "Slack API Bot Token"
    }

    API_ENDPOINTS = {
        "GMAIL_SEND_EMAIL": "https://www.googleapis.com/gmail/v1/users/me/messages/send"
    }

    def __init__(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.config = {}

        # Load environment variables
        self._load_env()

        # Load and validate configuration values
        self._load_config()

    def _load_env(self):
        """Load environment variables from .env file if it exists."""
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            self.logger.warning(".env file not found. Using system environment variables.")

    def _load_config(self):
        """Load and validate all required configuration values."""
        missing_vars = []
        
        for var, description in self.REQUIRED_VARS.items():
            value = os.getenv(var)
            if value is None:
                missing_vars.append(f"{var} ({description})")
            self.config[var] = value

        if missing_vars:
            raise ConfigurationError(
                "Missing required environment variables:\n" + "\n".join(f"- {var}" for var in missing_vars)
            )

        # Load additional paths
        self.config.update({
            "CREDENTIALS_PATH": str(Path("credentials.json").absolute()),
            "MODEL_PATH": str(Path("models").absolute()),
            "CACHE_DIR": str(Path("cache").absolute()),
            "LOG_DIR": str(Path("logs").absolute())
        })

        # Ensure necessary directories exist
        for dir_path in [self.config["MODEL_PATH"], self.config["CACHE_DIR"], self.config["LOG_DIR"]]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def get(self, key: str):
        """Safely retrieve a configuration value."""
        if key not in self.config:
            raise ConfigurationError(f"Configuration key '{key}' not found")
        return self.config[key]

    def __getitem__(self, key: str):
        """Allow dictionary-style access to configuration."""
        return self.get(key)

# Create a global configuration instance
config = Config()

