import re


def redact_named_greeting(message):
    # This regex will match named greetings like 'Hi [name]!', 'Hello {name}.' and 'Hey [name], '
    pattern = r'(?i)(Hi|Hello|Hey)\s+([\w]+)[,.!]'
    if re.search(pattern, message.content):
        # Substitute matched pattern with "Hi REDACTED!"
        message.content = re.sub(pattern, r'\1 REDACTED', message.content)

    return message


def anonymize_message(message):
    message = redact_message_owner_text(message)

    message = redact_introduction(message)

    message = redact_named_greeting(message)

    return message


def redact_message_owner_text(message):
    if "is the thread owner" in message.content:
        message.content = ""
    return message


def redact_introduction(message):
    # This regex will match various phrases that someone might use to state their name.
    # The parentheses create groups that can be referenced in the replacement string.
    patterns = [
        r"(my name is) (\w+)",
        r"(my name['`´’]s) (\w+)",
    ]
    for pattern in patterns:
        if re.search(pattern, message.content, flags=re.IGNORECASE):
            # Substitute matched pattern with "___ REDACTED"
            message.content = re.sub(pattern, r'\1 REDACTED', message.content, flags=re.IGNORECASE)

    return message

