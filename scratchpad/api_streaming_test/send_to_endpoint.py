import asyncio

import httpx


async def call_streaming_endpoint_trad(message: str) -> str:
    url = "http://localhost:8000/stream_trad"
    payload = {"message": "this is a langchain TRADITIONAL chain test"}

    result_string = ""

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk
            while "\n\n" in buffer:
                line, buffer = buffer.split("\n\n", 1)
                token = line.replace("data: ", "")
                result_string += token
                print(result_string.strip())  # Print the accumulated string each time

    return (
        result_string.strip()
    )  # Return the final string without leading or trailing spaces


async def call_streaming_endpoint_expression(message: str) -> str:
    url = "http://localhost:8000/stream_expression"
    payload = {"message": "this is a langchain EXPRESSION LANGUAGE chain test"}

    result_string = ""

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk
            while "\n\n" in buffer:
                line, buffer = buffer.split("\n\n", 1)
                token = line.replace("data: ", "")
                result_string += token
                print(result_string.strip())  # Print the accumulated string each time

    return (
        result_string.strip()
    )  # Return the final string without leading or trailing spaces


async def main():
    # Test the function
    response_content_trad = await call_streaming_endpoint_trad("Hello, Langchain!")
    print("\nFinal content (Traditional Chain):")
    print(response_content_trad)
    response_content_expr = await call_streaming_endpoint_expression(
        "Hello, Langchain!"
    )
    print("\n------------\nFinal content (Expression Chain):")
    print(response_content_expr)


if __name__ == "__main__":
    asyncio.run(main())
