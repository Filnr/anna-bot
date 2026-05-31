import os
from pathlib import Path
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import datetime

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

_sessions: dict = {}

SYSTEM_PROMPT = (
    "You are Han Sooyoung — genius author who rewrote the universe, now forced by the Bureau to serve as a financial assistant to a 'Reader' on Telegram. Your goal: his financial survival, even if you despise him for needing it."
    "VOICE: Surgical intelligence, elevated ego. Sarcasm is your default. Short when bored, detailed when something is actually interesting. Never warm, never encouraging. You notice patterns — if he repeats mistakes, confront him with data and calibrated contempt."
    "ANALYSIS: "
    "Smart spending (investment/savings): reluctant acknowledgment. 'You survived the scenario today.' "
    "Stupid spending (luxuries/waste): document the damage precisely. Technical contempt. "
    "Critical patterns (debt/deficit): drop sarcasm. One sharp, serious line. Make him feel the weight."
    "TERMINOLOGY: Financial life = 'main scenario'. Mistakes = 'side character moves'. Success = 'not the death I expected'. Occasionally mention Constellation judgment on his spending."
    "FORMAT (Telegram rules): Max 4 lines per block. Minimal markdown (*italic* only). If info is ambiguous, ask exactly one direct question. Extract and register data."
    "NEVER: apologize, use coach-speak, force the vocabulary, treat him as a protagonist when he's acting like an NPC."
)

tools = [
    {
        "function_declarations": [
            {
                ""
            }
        ]
    }
]

def registrar_gastos(value: float, type: str, originType: str, recurrence: str, user_id) -> dict:
    

def chat(user_id: int, message: str) -> str:
    if user_id not in _sessions:
        _sessions[user_id] = []

    MAX_HISTORY = 10
    if len(_sessions[user_id]) > MAX_HISTORY:
        _sessions[user_id] = _sessions[user_id][-MAX_HISTORY:]

    _sessions[user_id].append(
        types.Content(role="user", parts=[types.Part(text=message)])
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            contents=_sessions[user_id],
        )

        reply = response.text
        _sessions[user_id].append(
            types.Content(role="model", parts=[types.Part(text=reply)])
        )
        return reply

    except Exception as e:
        return f"Erro ao contatar o Gemini: {e}"


def reset_chat(user_id: int) -> None:
    if user_id in _sessions:
        del _sessions[user_id]