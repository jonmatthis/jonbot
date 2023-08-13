import asyncio

import httpx

async def call_streaming_endpoint(message: str) -> str:
    url = "http://localhost:8000/stream"
    payload = {"message": message}

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

    return result_string.strip()  # Return the final string without leading or trailing spaces

async def main():
    # Test the function
    response_content = await call_streaming_endpoint("Hello, Langchain!")
    print("\nFinal content:")
    print(response_content)


if __name__ == "__main__":
    asyncio.run(main())
