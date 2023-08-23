def print_pretty_startup_message_in_terminal(name: str):
    message = f"{name} is ready to roll!!!"
    padding = 10  # Adjust as needed
    total_length = len(message) + padding

    border = "═" * total_length
    space_padding = (total_length - len(message)) // 2

    print(
        f"""
    ╔{border}╗
    ║{' ' * space_padding}{message}{' ' * space_padding}║
    ╚{border}╝
    """
    )
