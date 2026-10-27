from pydantic_settings import BaseSettings,SettingsConfigDict
from pathlib import Path
from functools import lru_cache

# 配置.env文件的实际路径
ENV_FILE = Path(__file__).parents[2] / ".env"

"""
默认情况下pydantic_settings会从系统环境变量中读取配置
如果用load_datenv方式读取的话，还要做数据类型转的转换，用pydantic_settings可以设置默认读取的值数据类型值
"""
class Settings(BaseSettings):
    # LLM
    llm_model: str
    llm_base_url: str
    llm_api_key: str

    # 商城 API
    commerce_api_base_url: str

    # 数据库
    database_url: str
    database_url_sync: str

    # 服务器
    app_host: str
    app_port: int

    # extra="ignore"表示.env中配置了但是当前文件没有配置,不会报错
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", env_file_encoding="utf-8")

# 1,延迟加载
@lru_cache
def get_settings() -> Settings:
    print("初始化settings")
    return Settings()

# 2,预加载
settings = Settings()
# 两种方式都可以读
