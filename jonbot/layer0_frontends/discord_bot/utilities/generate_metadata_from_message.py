from typing import Dict, Any

from discord import Message


def serialize_object(obj: Any) -> Any:
    """
    Serialize an object into JSON-compatible data structures.

    Args:
        obj (Any): The object to serialize.

    Returns:
        Any: The serialized object, in the form of JSON-compatible data structures.
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {key: serialize_object(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_object(elem) for elem in obj]
    elif hasattr(obj, "__dict__"):
        return serialize_object(vars(obj))
    else:
        return str(obj)


def serialize_discord_message(message: Message) -> Dict[str, Any]:
    """
    Serialize a discord message into a dictionary.

    Args:
        message (Message): The discord message to serialize.

    Returns:
        Dict[str, Any]: A dictionary containing the serialized discord message.
    """
    serialized_message = {}

    for attr in dir(message):
        # Skip over private and protected attributes
        if attr.startswith("_"):
            continue

        value = getattr(message, attr)

        # Serialize the attribute value
        serialized_value = serialize_object(value)

        serialized_message[f"discord_message_{attr}"] = serialized_value

    return serialized_message
