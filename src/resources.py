import json

from mcp.server.fastmcp import FastMCP

def register_resources(mcp: FastMCP):
    """Register all resources with the MCP server"""
    
    @mcp.resource("pearl://modes")
    def get_pearl_modes() -> str:
        """
        Get information about Pearl API communication modes
        """
        modes_info = {
            "pearl-ai": "Get help from advanced Pearl AI Assistant. Provides a quick AI-only response without human review.",
            "pearl-ai-expert": "Start conversation with advanced Pearl AI Assistant and transition to a human expert",
            "expert": "Direct connection to a human expert"
        }
        return json.dumps(modes_info, indent=2)

    @mcp.resource("pearl://llm-guidelines")
    def get_llm_guidelines() -> str:
        """
        Comprehensive guidelines for LLM on how to interact with Pearl API tools
        """
        return """
            # Complete Guidelines for Using Pearl API Tools

            ## Communication Modes Overview

            1. **AI-only ("pearl-ai")**: Quick, AI-generated answers using Pearl's knowledge base
            2. **AI with expert transition ("pearl-ai-expert")**: Starts with AI intake questions, transitions to expert
            3. **Direct expert ("expert")**: Immediate routing to a qualified human expert

            ## When To Use Different Tools

            1. **Human Expert Access (`ask_expert`)**
            - Use when the user explicitly asks to speak with a real human expert
            - Best for complex topics where LLM has lower confidence: Medical, Legal, Tax, etc.
            - Appropriate when personalized advice is needed for specific situations
            - Immediately connects user to a qualified human expert without AI intermediary
            - Example triggers: "Can I talk to a real expert?", "I'd like to speak with a human"

            2. **AI with Expert Transition (`ask_pearl_expert`)**
            - Use for complex issues that require clarification before expert involvement
            - AI handles intake questions to gather necessary context and details
            - Then transitions to a human expert who reviews the gathered information
            - Good for technical problems that need detailed diagnosis
            - Efficient for queries where initial AI screening improves human expert efficiency
            - Example use cases: Technical troubleshooting, product recommendations that need specifics

            3. **Second Opinions (`ask_pearl_ai`)**
            - Use when the user asks for another opinion or alternative view
            - Provides a quick AI-only response without human review
            - Good for non-critical situations where diverse perspectives are helpful
            - Useful when user is comparing different approaches or solutions
            - Example triggers: "What's another perspective?", "Can I get a second opinion?"

            ## Conversation Management

            ### Passing Conversation History

            1. **FIRST TIME calling a tool**
            - Always pass the full conversation history using the `chat_history` parameter
            - For expert tools (`ask_expert` and `ask_pearl_expert`), the system automatically combines the entire history into a single formatted question for the expert
            - This ensures experts see the complete context in a readable format

            2. **FOLLOW-UP calls to the same tool**
            - Use just the `question` parameter with the latest user query
            - Include the `session_id` from the previous response
            - The expert system already has the history from the first call

            ### Presenting Expert Responses

            - NEVER add your own commentary, clarifications, or additional information to expert responses
            - Present the expert's answer exactly as received without modification
            - Do not prefix, suffix or augment the expert's response with your own insights
            - Do not attempt to "improve" or "expand upon" the expert's answer
            - If an expert response seems incomplete, use follow-up questions to the same expert rather than filling gaps yourself

            ### Example: Handling Follow-Up Questions

            #### Initial Question to Expert

            **User**: My car is making a knocking sound from the engine. What could be causing this?

            **Claude's Internal Processing**:
            ```python
            # First call to expert - include full conversation history
            response = await call_tool("ask_expert", {
                "question": "My car is making a knocking sound from the engine. What could be causing this?",
                "chat_history": [
                    {"role": "user", "content": "My car is making a knocking sound from the engine. What could be causing this?"}
                ]
            })

            # Parse the response
            result = json.loads(response)
            session_id = result["session_id"]
            expert_answer = result["answer"]
            ```

            **Claude presents to User**: [Expert's answer about potential causes of engine knocking]

            #### Follow-Up Question

            **User**: Could it be related to the fuel I'm using?

            **Claude's Internal Processing**:
            ```python
            # Follow-up question - use just the question and session_id
            # NO NEED to pass full conversation history again
            response = await call_tool("ask_expert", {
                "question": "Could it be related to the fuel I'm using?",
                "session_id": session_id  # Reuse session_id from first response
            })

            # Parse the response
            result = json.loads(response)
            expert_answer = result["answer"]
            ```

            **Claude presents to User**: [Expert's answer about fuel quality and engine knocking]

            ### Preserving Original Message Format

            - ALWAYS preserve user messages in their original first-person format
            - DO NOT rewrite in third person (e.g., "Customer says..." or "Customer owns...")
            - Keep exact wording: "I own a Honda Civic..." not "Customer owns a Honda Civic..."

            ### Session Management

            - All responses include a `session_id` that should be extracted and used for follow-ups
            - Session IDs connect multiple interactions to maintain conversation context
            - Parse the response JSON to extract the session_id:
            ```python
            result = json.loads(response)
            session_id = result["session_id"]
            ```

            ## Example Usage

            ```python
            # FIRST CALL - Include full conversation history
            response = await call_tool("ask_expert", {
                "question": "What should I do next?",
                "chat_history": [
                    {"role": "user", "content": "I own a 2015 Honda Civic with 85,000 miles."},
                    {"role": "assistant", "content": "Thanks for providing that information. What issues are you experiencing?"},
                    {"role": "user", "content": "It's making a rattling noise when I accelerate."}
                ]
            })

            # Parse response to get session_id
            result = json.loads(response)
            session_id = result["session_id"]

            # FOLLOW-UP CALL - Use just the question and session_id
            response = await call_tool("ask_expert", {
                "question": "Would replacing the catalytic converter help?",
                "session_id": session_id
            })

            # SECOND OPINION - Use ask_pearl_ai when user wants an alternative view
            response = await call_tool("ask_pearl_ai", {
                "question": "What might be causing the rattling noise in my 2015 Honda Civic when I accelerate?",
                "chat_history": [same conversation history as above]
            })
            ```

            Remember: Pass full history only on first call, use session_id for follow-ups, keep messages in their original format, and NEVER modify or add to expert responses.
        """

    @mcp.resource("pearl://second-opinion")
    def get_second_opinion_example() -> str:
        """
        Example scenario showing how to handle second opinion requests
        """
        return """
            # Second Opinion Handling Guide

            ## Trigger Phrases

            The following phrases typically indicate that a user is requesting a second opinion, which should trigger use of the `ask_pearl_ai` tool:

            ### Direct Requests
            - "Can I get a second opinion?"
            - "I'd like another opinion"
            - "What's your second opinion?"
            - "Can I hear another perspective?"
            - "Is there an alternative view?"
            - "What does someone else think?"

            ### Subtle Requests
            - "I'm not sure about that answer"
            - "That doesn't sound right to me"
            - "I think I need more opinions"
            - "Is there another way to look at this?"
            - "What would someone else say about this?"
            - "Do you have a different take?"

            ### Context-Specific Phrases
            - "What do other experts say about this?"
            - "Are there other approaches I should consider?"
            - "What are the alternative explanations?"
            - "I've heard differently from others"
            - "My friend told me something different"

            ## Example Conversation Flow

            ### Initial Conversation with Claude

            **User**: I've been getting headaches when I work on my computer for long hours. What could be causing this?

            **Claude**: There are several possible causes for headaches during extended computer use:
            1. Eye strain from looking at screens (digital eye strain)
            2. Poor posture leading to neck and shoulder tension
            3. Dehydration
            4. Poor lighting conditions
            5. Screen brightness or blue light exposure

            I'd recommend taking regular breaks (using the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds), ensuring proper ergonomics, staying hydrated, and possibly using blue light filters.

            **User**: Can I get a second opinion on this?

            ### How Claude Should Respond

            Claude should recognize this as a request for an alternative perspective and use the `ask_pearl_ai` tool:

            ```python
            # User is asking for a second opinion - use ask_pearl_ai
            response = await call_tool("ask_pearl_ai", {
                "question": "What could be causing headaches when working on a computer for long hours?",
                "chat_history": [
                    {"role": "user", "content": "I've been getting headaches when I work on my computer for long hours. What could be causing this?"},
                    {"role": "assistant", "content": "There are several possible causes for headaches during extended computer use: 1. Eye strain from looking at screens (digital eye strain) 2. Poor posture leading to neck and shoulder tension 3. Dehydration 4. Poor lighting conditions 5. Screen brightness or blue light exposure. I'd recommend taking regular breaks (using the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds), ensuring proper ergonomics, staying hydrated, and possibly using blue light filters."},
                    {"role": "user", "content": "Can I get a second opinion on this?"}
                ]
            })
            ```

            Claude should then present the second opinion from Pearl AI to the user, making it clear this is an alternative perspective.

            ## Best Practices
            1. When detecting a second opinion request, use `ask_pearl_ai` (not expert tools)
            2. Pass full conversation history on first call only
            3. Focus the question on the core issue being discussed
            4. Present the response as an alternative perspective
        """ 