from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    db_url: str = "sqlite:///database.db"
    test_db_url: str = ""
    testing: bool = False

    public_key_path: Path = BASE_PATH / "certs" / "jwt-public.pem"
    private_key_path: Path = BASE_PATH / "certs" / "jwt-private.pem"
    algoritm: str
    access_token_exp_min: int = 15

    model_config = SettingsConfigDict(env_file=BASE_PATH / ".dev.env")

    def get_db_url(self):
        if self.testing:
            return self.test_db_url
        return self.db_url


settings = Settings()