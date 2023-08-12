from langchain.callbacks.base import AsyncCallbackHandler


class StreamingAsyncCallbackHandler(AsyncCallbackHandler):
    async def on_llm_new_token(self, token: str, *args, **kwargs) -> None:
        """Run when a new token is generated."""
        print("Hi! I just woke up. Your llm is generating a new token: '{token}'")
        yield f"lookit this token: {token} |"
