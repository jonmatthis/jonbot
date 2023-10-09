from jonbot.backend.data_layer.analysis.extract_conversation_topics import logger


def get_human_ai_message_pairs(chat):
    human_ai_pairs = []
    for message in chat.messages:
        if message.content == "":
            continue
        if message.is_bot:
            continue
        human_message_id = message.message_id
        for msg in chat.messages:
            if msg.parent_message_id == human_message_id:
                human_ai_pairs.append((message.content, msg.content))
    logger.info(f"Extracted {len(human_ai_pairs)} human-AI pairs from {len(chat.messages)} messages.")

    return human_ai_pairs
