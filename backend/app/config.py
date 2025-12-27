from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://wasp_builder:wasp_builder_pass@localhost:5432/wasp_builder"
    openrouter_api_key: str = ""
    generated_apps_path: str = "/app/generated_apps"
    port_range_start: int = 10001
    port_range_end: int = 10999

    class Config:
        env_file = ".env"


settings = Settings()

