from services.expenses_service import ExpensesService  # ✅ path correto
from pathlib import Path
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import datetime
from core.database import SessionLocal
from repositories.expenses_repository import ExpensesRepository
from models.expenses import Expenses

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

tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="registrar_gastos",
            description=(
                "Register a new expense or financial transaction for the user. "
                "Call this whenever the user mentions spending, buying, paying, or any financial outflow."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "value": types.Schema(
                        type=types.Type.NUMBER,
                        description="The monetary amount of the expense (e.g. 49.90)."
                    ),
                    "type": types.Schema(
                        type=types.Type.STRING,
                        description="Expense category (e.g. 'food', 'transport', 'entertainment', 'health', 'investment')."
                    ),
                    "originType": types.Schema(
                        type=types.Type.STRING,
                        description="Origin of the expense (e.g. 'nintendo', 'ifood', 'amazon', 'restaurant')."
                    ),
                    "recurrence": types.Schema(
                        type=types.Type.STRING,
                        description="Whether the expense is 'once', 'daily', 'weekly', 'monthly' or 'yearly'."
                    ),
                },
                required=["value", "type", "originType", "recurrence"],
            ),
        )
    ]
)

def registrar_gastos(value: float, type: str, originType: str, recurrence: str, user_id: int) -> dict:
    try:
        db = SessionLocal()
        repository = ExpensesRepository(db)
        service = ExpensesService(repository)

        expense = Expenses(
            user_id=user_id,
            value=value,
            type=type,
            originType=originType,
            recurrence_type=recurrence,
            date=datetime.datetime.now(),
        )
        service.register(expense)
        db.close()

        return {"status": "registered", "value": value, "type": type}

    except Exception as e:
        return {"status": "error", "message": str(e)}

FUNCTION_MAP = {
    "registrar_gastos": registrar_gastos,
}

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
        while True:  # ✅ loop agentico
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=[tools],  # ✅ tools passado na config
                ),
                contents=_sessions[user_id],
            )

            candidate = response.candidates[0]

            # Salva o turno do modelo no histórico
            _sessions[user_id].append(
                types.Content(role="model", parts=candidate.content.parts)
            )

            # Verifica se há function calls na resposta
            function_calls = [p for p in candidate.content.parts if p.function_call]

            if not function_calls:
                return response.text  # ✅ sem tool call, retorna resposta final

            # Executa cada função solicitada
            tool_results = []
            for part in function_calls:
                fn_name = part.function_call.name
                fn_args = dict(part.function_call.args)

                if fn_name in FUNCTION_MAP:
                    fn_args["user_id"] = user_id  # ✅ injeta user_id server-side
                    result = FUNCTION_MAP[fn_name](**fn_args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}

                tool_results.append(
                    types.Part.from_function_response(name=fn_name, response=result)
                )

            # Devolve os resultados pro Gemini continuar
            _sessions[user_id].append(
                types.Content(role="user", parts=tool_results)
            )
            # loop: Gemini vai processar e gerar a resposta final em texto

    except Exception as e:
        return f"Erro ao contatar o Gemini: {e}"


def reset_chat(user_id: int) -> None:
    if user_id in _sessions:
        del _sessions[user_id]