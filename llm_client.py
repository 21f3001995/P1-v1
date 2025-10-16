# llm_client.py
import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
print("OpenAI API key loaded:", bool(openai.api_key))


def generate_code_from_brief(brief: str) -> str:
    """
    Uses GPT to generate HTML/JS code for the given brief.
    If LLM fails, returns a simple fallback template.
    """
    prompt = f"""
    You are a code generator that outputs minimal working HTML/JS apps.
    Generate a single-page static web app (index.html) for this brief:
    ---
    {brief}
    ---
    The app should be functional and runnable as static HTML (no backend).
    Do not include explanations. Output only valid HTML code.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional web app code generator."},
                {"role": "user", "content": prompt}
            ],
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("LLM generation error:", e)
        # Fallback template
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Generated App (Fallback)</title></head>
        <body>
            <h1>Task Brief</h1>
            <p>{brief}</p>
        </body>
        </html>
        """
