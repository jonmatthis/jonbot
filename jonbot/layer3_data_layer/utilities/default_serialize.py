from datetime import datetime
from typing import Any


def default_serialize(o: Any) -> str:
    if isinstance(o, datetime):
        return o.isoformat()
    elif hasattr(o, "model_dump"):
        return o.model_dump()
    elif hasattr(o, "dict"):
        return o.dict()
    elif hasattr(o, "to_dict"):
        return o.to_dict()
    elif hasattr(o, "__dict__") and not isinstance(o, dict):
        return o.__dict__
    return str(o)
