import os

from pydantic import BaseModel

from jonbot.system.environment_variables import URL_PREFIX, HOST_NAME


class ApiRoute(BaseModel):
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
        if not self.route.startswith("/"):
            return f"{self.url}:{self.port_number}/{self.endpoint}/{self.route}"
        return f"{self.url}:{self.port_number}{self.endpoint}/{self.route}"

    @classmethod
    def from_endpoint(cls,
                      endpoint: str,
                      **kwargs):
        return cls(endpoint=endpoint,
                   **kwargs)
