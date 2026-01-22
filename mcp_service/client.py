import asyncio
from collections.abc import Generator

import httpx
from fastmcp import Client


MCP_URL = "http://127.0.0.1:6432/mcp"
API_KEY = "<paste-your-api-key>"


class APIKeyAuth(httpx.Auth):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """
        Send the request, with a custom header.
        """
        request.headers["EASY_VOCAB_API_KEY"] = self.api_key
        yield request


async def main() -> None:
    auth = APIKeyAuth(api_key=API_KEY)

    async with Client(transport=MCP_URL, auth=auth) as client:
        # List available tools.
        print(f"Available tools: {await client.list_tools()}")

        # Call a specific tool.
        result = await client.call_tool(name="add_word", arguments={"word": "World"})
        print(f"Tool call result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
