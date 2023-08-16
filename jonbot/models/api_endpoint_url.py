import os
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, validator

from jonbot.system.environment_variables import URL_PREFIX, HOST_NAME

class ApiRoute(BaseModel):
    host_name: str = HOST_NAME
    url_prefix: str = URL_PREFIX
    port_number: int = int(os.getenv('PORT_NUMBER', '8080'))
    endpoint: Optional[str]


    @property
    def url(self) -> str:
        return f"{self.url_prefix}://{self.host_name}"

    @property
    def endpoint_url(self) -> str:
        return f"{self.route}{self.endpoint}"

    @property
    def route(self) -> str:
        return f"{self.url}:{self.port_number}"

    @classmethod
    def from_endpoint(cls, endpoint: str, **kwargs):
        return cls(endpoint=endpoint, **kwargs)

    @validator("url_prefix")
    def validate_url_prefix(cls, v):
        if v not in ['http', 'https']:
            raise ValueError("url_prefix should be either 'http' or 'https'")
        return v

    @validator("host_name")
    def validate_host_name(cls, v):
        if not v:
            raise ValueError("hostname cannot be empty")
        return v

    @validator("port_number", pre=True, always=True)
    def validate_port_number(cls, v):
        if not (0 <= v <= 65535):
            raise ValueError("port_number should be between 0 and 65535")
        return v

    @validator("endpoint", pre=True, always=True)
    def validate_slash(cls, v):
        if v and not v.startswith("/"):
            return "/" + v
        return v

    def validate_endpoint_url(self):
        parsed = urlparse(self.endpoint_url)
        if not all([parsed.scheme, parsed.netloc, parsed.path]):
            raise ValueError(f"Invalid full route URL: {self.endpoint_url}")

if __name__ == "__main__":
    try:
        # Attempting to create an instance with valid parameters
        api_route1 = ApiRoute(endpoint="/api", route="/test")
        api_route1.validate_endpoint_url()
        print("Valid Endpoint:", api_route1.endpoint_url)

    except Exception as e:
        print(f"Error: {e}")
