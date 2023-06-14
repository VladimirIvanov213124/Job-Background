from pydantic import BaseSettings


class AppSecret(BaseSettings):
    gpt_key: str
    celery_name: str
    broker_url: str
    result_backend: str
    driver_url: str

    class Config:
        env_file: str = '.env'
