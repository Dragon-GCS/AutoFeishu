from typing import Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
)


class Config(BaseSettings):
    model_config = {
        "env_prefix": "FEISHU_",
        "case_sensitive": False,
        "env_file": (".env", ".feishu.env"),
        "pyproject_toml_table_header": ("tool", "auto-feishu"),
        "extra": "ignore",
    }

    app_id: str = ""
    app_secret: str = ""

    base_url: str = "https://open.feishu.cn/open-apis"
    http_timeout: int = 30

    phone: str = ""
    email: str = ""
    open_id: str = ""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            dotenv_settings,
            PyprojectTomlConfigSettingsSource(settings_cls),
        )


config = Config()
