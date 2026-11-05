from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

app = FastAPI(title="LinkedIn Content Automation API")

class LinkedInRequest(BaseModel):
    brand: str
    context: str
    tone: Optional[str] = "professional"

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/linkedin")
def generate_linkedin_post(request: LinkedInRequest):
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint or not api_key:
        raise HTTPException(status_code=500, detail="AI configuration missing")

    prompt = f"""
You are an AI content team creating LinkedIn content for a fintech organization.

Simulate three specialized agents:
1. Ideation Agent: generate exactly 3 relevant LinkedIn post ideas.
2. Drafting Agent: select the strongest idea and create one concise LinkedIn post.
3. Hashtag Agent: generate 3 to 5 relevant hashtags.

Brand: {request.brand}
Context: {request.context}
Tone: {request.tone}

Return ONLY valid JSON in this format:
{{
  "ideas": ["idea 1", "idea 2", "idea 3"],
  "draft": "post text",
  "confidence": 0.90,
  "hashtags": ["#FinTech", "#AI", "#Innovation"]
}}
"""

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    body = {
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(endpoint, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        content = content.strip()

        # Remove Markdown fences if the model returns them.
        if content.startswith("```"):
            content = content.replace("```json", "", 1).replace("```", "").strip()

        return json.loads(content)

    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"AI API request failed: {exc}")
    except (KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid AI response: {exc}")
