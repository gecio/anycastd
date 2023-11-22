import datetime

from pydantic_settings import BaseSettings

DEFAULT_URL = "http://127.0.0.1:9013"


class CabourotteHealthcheck(BaseSettings):
    name: str
    url: str = DEFAULT_URL
    interval: datetime.timedelta = datetime.timedelta(seconds=5)
