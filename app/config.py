from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracoes da aplicacao carregadas por variaveis de ambiente."""

    app_name: str = "movidesk-clickup-api"
    app_env: str = "dev"
    log_level: str = "INFO"
    port: int | None = None

    movidesk_token: str = ""
    movidesk_base_url: str = "https://api.movidesk.com/public/v1"
    movidesk_ticket_url_template: str = ""

    clickup_token: str = ""
    clickup_base_url: str = "https://api.clickup.com/api/v2"
    clickup_default_list_id: str = ""
    clickup_default_list_name: str = "Power BI"
    clickup_task_status: str = "Open"
    clickup_assignee_ids: str = ""
    clickup_assignee_email: str = "vinicius.souza@penso.com.br"
    clickup_assign_authorized_user: bool = True

    webhook_secret: str = ""
    database_url: str = "sqlite:///./movidesk_clickup.db"
    turso_database_url: str = ""
    turso_auth_token: str = ""

    enable_movidesk_update: bool = False
    movidesk_success_status_value: str = "OK"
    request_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
