import os

from jonbot.system.environment_variables import URL_PREFIX, HOST_NAME
from pydantic import BaseModel
class ApiRouteUrl(BaseModel):
    host_name: str = HOST_NAME
    url_prefix: str = URL_PREFIX
    port_number: int = int(os.getenv('PORT_NUMBER', '8080'))
    endpoint: str = None
    route: str = None

    @property
    def url(self) -> str:
        return f"{self.url_prefix}://{self.host_name}"

    @property
    def endpoint_url(self) -> str:
        if not self.endpoint.startswith("/"):
            return f"{self.url}:{self.port_number}/{self.endpoint}"
        return f"{self.url}:{self.port_number}{self.endpoint}"

    @property
    def full_route(self) -> str:
        if not self.route:
            return self.endpoint_url
        if self.endpoint:
            raise ValueError("Cannot provide both route and endpoint")
        return self.route

    @classmethod
    def from_endpoint(cls, endpoint: str, host_name: str, port_number: int, prefix: str = "http"):
        return cls(host_name=host_name, port_number=port_number, prefix=prefix, endpoint=endpoint)

    @classmethod
    def from_route(cls, route: str, host_name: str, port_number: int, prefix: str = "http"):
        return cls(host_name=host_name, port_number=port_number, prefix=prefix, route=route)
