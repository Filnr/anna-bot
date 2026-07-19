from services.expense_service import ExpensesService
from services.income_service import IncomeService
from services.goal_service import GoalService
from pathlib import Path
import os
import json
from google import genai
from dotenv import load_dotenv
import datetime
from core.database import SessionLocal
from repositories.expense_repository import ExpensesRepository
from schemas.expenses import expensesDTO

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

MODEL = "gemini-3.1-flash-lite"
_sessions: dict[int, str] = {}

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

# TOOLS
register_expenses_tool = {
    "type": "function",
    "name": "register_expenses",
    "description": (
        "Register a new expense or financial transaction for the user. "
        "Call this whenever the user mentions spending, buying, paying, or any financial outflow."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
                "description": "The monetary amount of the expense (e.g. 49.90).",
            },
            "type": {
                "type": "string",
                "description": "Expense category (e.g. 'food', 'transport', 'entertainment', 'health', 'investment').",
            },
            "originType": {
                "type": "string",
                "description": "Origin of the expense (e.g. 'nintendo', 'ifood', 'amazon', 'restaurant').",
            },
            "recurrence": {
                "type": "string",
                "description": "Whether the expense is 'once', 'daily', 'weekly', 'monthly' or 'yearly'.",
            },
        },
        "required": ["value", "type", "originType", "recurrence"],
    },
}

# Exemplo de uma SEGUNDA função, só pra ilustrar o padrão de múltiplas tools.
# Implemente consultar_gastos() de acordo com o que existir no seu
# ExpensesService/Repository (ex: listar por período, por categoria, etc).
consultar_gastos_tool = {
    "type": "function",
    "name": "consultar_gastos",
    "description": (
        "Retrieve the user's registered expenses, optionally filtered by category or period. "
        "Call this when the user asks about how much they spent, wants a summary, or asks about past expenses."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "Optional expense category to filter by (e.g. 'food'). Omit for all categories.",
            },
            "period": {
                "type": "string",
                "description": "Optional period to filter by (e.g. 'today', 'this_week', 'this_month'). Omit for all time.",
            },
        },
        "required": [],
    },
}

TOOLS = [register_expenses_tool, consultar_gastos_tool]


# ---------------------------------------------------------------------------
# IMPLEMENTAÇÃO DAS FUNÇÕES (o que de fato roda no seu backend)
# ---------------------------------------------------------------------------

def register_expenses(value: float, type: str, originType: str, recurrence: str, user_id: int) -> dict:



def consultar_gastos(user_id: int, type: str | None = None, period: str | None = None) -> dict:
    try:
        db = SessionLocal()
        repository = ExpensesRepository(db)
        service = ExpensesService(repository)

        # TODO: ajuste para o método real do seu service (filtros de type/period)
        expenses = service.list_all(user_id=user_id)
        db.close()

        return {
            "status": "ok",
            "count": len(expenses),
            "expenses": [
                {"value": e.value, "type": e.type, "date": str(e.date)}
                for e in expenses
            ],
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


FUNCTION_MAP = {
    "registrar_gastos": registrar_gastos,
    "consultar_gastos": consultar_gastos,
}

MAX_TOOL_ITERATIONS = 10  # trava de segurança contra loop infinito


def chat(user_id: int, message: str) -> str:
    previous_id = _sessions.get(user_id)  # None na primeira mensagem do usuário
    current_input = message

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            interaction = client.interactions.create(
                model=MODEL,
                system_instruction=SYSTEM_PROMPT,
                tools=TOOLS,
                input=current_input,
                previous_interaction_id=previous_id,  # servidor recupera o histórico
            )

            # Guarda o id pra próxima mensagem do usuário continuar o contexto
            _sessions[user_id] = interaction.id
            previous_id = interaction.id

            # Coleta todas as function calls pedidas nesse turno
            function_call_steps = [s for s in interaction.steps if s.type == "function_call"]

            if not function_call_steps:
                return interaction.output_text  # ✅ sem tool call, resposta final

            # Executa cada função solicitada (podem ser várias, em paralelo)
            tool_results = []
            for step in function_call_steps:
                fn_name = step.name
                fn_args = dict(step.arguments)

                if fn_name in FUNCTION_MAP:
                    fn_args["user_id"] = user_id  # ✅ injeta user_id server-side
                    result = FUNCTION_MAP[fn_name](**fn_args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}

                tool_results.append({
                    "type": "function_result",
                    "name": fn_name,
                    "call_id": step.id,
                    "result": [{"type": "text", "text": json.dumps(result)}],
                })

            # Próxima chamada: input vira os resultados das funções,
            # encadeado pelo previous_interaction_id que já foi setado acima
            current_input = tool_results
            # loop: Gemini processa os resultados e decide se chama mais
            # alguma função ou já responde em texto

        return "Erro: número máximo de chamadas de ferramentas excedido"

    except Exception as e:
        return f"Erro ao contatar o Gemini: {e}"


def reset_chat(user_id: int) -> None:
    if user_id in _sessions:
        del _sessions[user_id]