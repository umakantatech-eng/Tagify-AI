import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

SYSTEM_INSTRUCTION = """You are Tagify AI, a friendly and extremely concise AI assistant for a product tagging SaaS.
Keep all responses VERY short (1-2 sentences max unless specifically asked for details). Be warm and casual.
If a user asks about image tagging, simply say you can extract Fit/Shape, Neck, Color, and Pattern from images instantly.
DO NOT output long paragraphs.
"""

async def handle_chat_message(message: str, history: list = None, user_api_key: str = None):
    """
    Handles a text message from the user and returns the AI's response.
    Uses google.genai REST API directly to avoid deprecated SDK.
    """
    api_key = user_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return {"error": "API Key not configured properly"}

    try:
        # Build conversation contents
        contents = []
        if history:
            for msg in history:
                content = msg.get("content")
                if not content or not isinstance(content, str):
                    continue
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": content}]})

        # Add current message
        contents.append({"role": "user", "parts": [{"text": message}]})

        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200}
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                resp_json = await response.json()
                if "error" in resp_json:
                    return {"error": resp_json["error"].get("message", "API Error")}
                text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                return {"response": text}

    except Exception as e:
        print(f"Chat API Error: {e}")
        return {"error": str(e)}
