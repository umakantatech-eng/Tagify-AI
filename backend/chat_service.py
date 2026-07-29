import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

SYSTEM_INSTRUCTION = """You are Tagify AI, a friendly and extremely concise AI assistant for a product tagging SaaS.
Keep all responses VERY short (1-2 sentences max unless specifically asked for details). Be warm and casual.
If a user asks about image tagging, simply say you can extract Fit/Shape, Neck, Color, and Pattern from images instantly.
DO NOT output long paragraphs.
"""

def get_chat_model(user_api_key=None):
    api_key = user_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return None
        
    genai.configure(api_key=api_key)
    try:
        # User's API environment only supports gemini-3.5-flash-lite, so we must use it for chat as well.
        model = genai.GenerativeModel('gemini-3.5-flash-lite', system_instruction=SYSTEM_INSTRUCTION)
        return model
    except Exception as e:
        print(f"Error initializing chat model: {e}")
        return None

async def handle_chat_message(message: str, history: list = None, user_api_key: str = None):
    """
    Handles a text message from the user and returns the AI's response.
    """
    model = get_chat_model(user_api_key)
    if not model:
        return {"error": "API Key not configured properly"}

    try:
        # Note: If history is provided, we could use model.start_chat(history=history).
        # For simplicity in this endpoint, we'll just format it as a prompt if needed, 
        # or use the built-in chat session.
        formatted_history = []
        if history:
            for msg in history:
                # Safely get content, skip table UI messages that don't have text content
                content = msg.get("content")
                if not content:
                    continue
                    
                role = "user" if msg.get("role") == "user" else "model"
                formatted_history.append({"role": role, "parts": [content]})
                
        chat = model.start_chat(history=formatted_history)
        
        # Send message in a thread to avoid blocking FastAPI event loop
        import asyncio
        response = await asyncio.to_thread(chat.send_message, message)
        return {"response": response.text}
    except Exception as e:
        print(f"Chat API Error: {e}")
        return {"error": str(e)}
