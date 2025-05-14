from mcp import types
from mcp.server.fastmcp import FastMCP

def register_prompts(mcp: FastMCP):
    """Register all prompts with the MCP server"""
    
    @mcp.prompt()
    def ask_legal_question() -> types.GetPromptResult:
        """
        Template for asking legal questions to Pearl experts
        """
        return types.GetPromptResult(
            description="Template for asking legal questions to Pearl experts",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text="I have a legal question about [TOPIC]. Specifically, I'd like to know [SPECIFIC QUESTION]. My situation is [BRIEF DESCRIPTION OF SITUATION]. What legal options do I have and what should I consider?"
                    )
                )
            ]
        )

    @mcp.prompt()
    def ask_medical_question() -> types.GetPromptResult:
        """
        Template for asking medical questions to Pearl experts
        """
        return types.GetPromptResult(
            description="Template for asking medical questions to Pearl experts",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text="I have a medical question about [CONDITION/SYMPTOM]. Specifically, I'm experiencing [SYMPTOMS] for [DURATION]. My medical history includes [RELEVANT HISTORY]. What could this indicate and what should I do next?"
                    )
                )
            ]
        ) 