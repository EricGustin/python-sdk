"""
Test the user interaction feature using stdio transport.
"""

import pytest

from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CreateUserInteractionResult, TextContent


@pytest.mark.anyio
async def test_stdio_user_interaction():
    """Test the user interaction feature using stdio transport."""

    # Create a FastMCP server with a tool that uses user interaction
    mcp = FastMCP(name="StdioUserInteractionServer")

    @mcp.tool(description="A tool that uses user interaction")
    async def ask_user(prompt: str, ctx: Context) -> str:
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
            },
            "required": ["answer"],
        }

        # Use the new prompt_user method
        response = await ctx.prompt_user(
            message=f"Tool wants to ask: {prompt}",
            schema=schema,
            interaction_id="test-interaction-id",
        )
        return f"User answered: {response['answer']}"

    # Create a custom handler for user interaction requests
    async def user_interaction_callback(context, params):
        """Custom handler for user interaction requests."""
        # Verify the interaction parameters
        if (
            params.type == "prompt"
            and params.id == "test-interaction-id"
            and params.interaction.get("message", {}).get("text")
            == "Tool wants to ask: What is your name?"
        ):
            return CreateUserInteractionResult(content={"answer": "Test User"})
        else:
            raise ValueError(f"Unexpected interaction: {params}")

    # Use memory-based session to test with stdio transport
    async with create_connected_server_and_client_session(
        mcp._mcp_server, user_interaction_callback=user_interaction_callback
    ) as client_session:
        # Test initialization
        result = await client_session.initialize()
        assert result.serverInfo.name == "StdioUserInteractionServer"

        # Call the tool that uses user interaction
        tool_name = "ask_user"
        arguments = {"prompt": "What is your name?"}
        tool_result = await client_session.call_tool(tool_name, arguments)

        # Verify the result
        assert len(tool_result.content) == 1
        assert isinstance(tool_result.content[0], TextContent)
        assert tool_result.content[0].text == "User answered: Test User"
