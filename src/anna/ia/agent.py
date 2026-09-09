"""Loop de orquestração: recebe a mensagem do usuário, conversa com a LLM, executa as
tools que ela pedir e devolve a resposta final em texto.

API pública do pacote `ia`: `chat(user_id, message)` e `reset_chat(user_id)`.
"""
import json
import logging
import traceback

from ia.client import call_llm
from ia.config import MAX_HISTORY_TURNS, MAX_TOOL_ITERATIONS, SYSTEM_PROMPT
from ia.tools import FUNCTION_MAP, WRITE_FUNCTIONS, _format_write_result

logger = logging.getLogger(__name__)

# Histórico manual por usuário (sem system prompt, que é sempre prependado na chamada).
_histories: dict[int, list[dict]] = {}

# Tools que apagam/alteram uma despesa por `expense_id`. Modelos pequenos ALUCINAM esse id
# (já chegaram a deduzir "id 2" do nada e apagar dado real). Só deixamos executar com um id
# que apareceu numa consulta desta mesma conversa — ver `_guard_expense_id`.
_ID_GUARDED = {"delete_expense", "update_expense"}


def _trim_history(history: list[dict]) -> list[dict]:
    user_indices = [i for i, m in enumerate(history) if m["role"] == "user"]
    if len(user_indices) > MAX_HISTORY_TURNS:
        cutoff = user_indices[-MAX_HISTORY_TURNS]
        return history[cutoff:]
    return history


def _collect_expense_ids(result: dict) -> set[int]:
    ids: set[int] = set()
    if not isinstance(result, dict):
        return ids
    for item in result.get("expenses") or []:
        if isinstance(item, dict) and isinstance(item.get("id"), int):
            ids.add(item["id"])
    return ids


def chat(user_id: int, message: str) -> str:
    history = _histories.setdefault(user_id, [])
    history.append({"role": "user", "content": message})

    # ids de despesa que o modelo pode tocar nesta conversa: só os que ele viu numa consulta
    # feita agora. Zerado a cada mensagem — o modelo tem que listar antes de excluir/atualizar.
    seen_expense_ids: set[int] = set()

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
            assistant_message = call_llm(messages)
            tool_calls = assistant_message.get("tool_calls") or []

            if not tool_calls:
                content = assistant_message.get("content") or ""
                history.append({"role": "assistant", "content": content})
                _histories[user_id] = _trim_history(history)
                return content

            history.append({
                "role": "assistant",
                "content": assistant_message.get("content") or "",
                "tool_calls": tool_calls,
            })

            calls_this_round = []
            for i, tool_call in enumerate(tool_calls):
                fn = tool_call["function"]
                fn_name = fn["name"]
                fn_args = fn.get("arguments") or {}
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args or "{}")
                    except json.JSONDecodeError:
                        fn_args = {}

                if fn_name not in FUNCTION_MAP:
                    result = {"status": "error", "message": f"Ferramenta desconhecida: {fn_name}"}
                elif fn_name in _ID_GUARDED and fn_args.get("expense_id") not in seen_expense_ids:
                    # Bloqueio de segurança: id não veio de nenhuma listagem desta conversa.
                    result = {
                        "status": "error",
                        "message": (
                            "Antes de excluir ou atualizar uma despesa você PRECISA chamar "
                            "get_expenses_by_month (ou get_last_month_expenses) e usar um "
                            "'id' exatamente como veio na lista. Não invente o id."
                        ),
                    }
                else:
                    try:
                        result = FUNCTION_MAP[fn_name](user_id=user_id, **fn_args)
                    except Exception as e:
                        # argumento inesperado / faltando, etc. — devolve como erro pro
                        # modelo poder se corrigir, sem derrubar a conversa inteira.
                        logger.error(f"Erro executando {fn_name}({fn_args}): {e}\n{traceback.format_exc()}")
                        result = {"status": "error", "message": f"Falha ao executar {fn_name}: {e}"}

                seen_expense_ids |= _collect_expense_ids(result)

                calls_this_round.append((fn_name, fn_args, result))
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", f"call_{i}"),
                    "content": json.dumps(result, ensure_ascii=False),
                })

            # Rodada só com ações de escrita BEM-SUCEDIDAS: responde na hora, sem gastar outra
            # chamada ao modelo pra "narrar" o que já sabemos que aconteceu. Se algo falhou,
            # deixa o loop seguir pro modelo tentar se corrigir (ex.: listar e reexecutar).
            if calls_this_round and all(
                fn_name in WRITE_FUNCTIONS and isinstance(result, dict) and result.get("status") == "success"
                for fn_name, _, result in calls_this_round
            ):
                try:
                    lines = [_format_write_result(fn_name, fn_args, result) for fn_name, fn_args, result in calls_this_round]
                except Exception:
                    lines = [result.get("message", "Ação concluída.") for _, _, result in calls_this_round]
                reply = "\n".join(lines)
                history.append({"role": "assistant", "content": reply})
                _histories[user_id] = _trim_history(history)
                return reply

        _histories[user_id] = _trim_history(history)
        return "Erro: número máximo de chamadas de ferramentas excedido"

    except Exception as e:
        logger.error(f"Error in chat: {e}\n{traceback.format_exc()}")
        return f"Erro ao contatar a LLM: {e}"


def reset_chat(user_id: int) -> None:
    _histories.pop(user_id, None)
