"""Formatação em Python das saídas das tools (escritas e consultas).

Monta o texto final direto em Python — mais rápido e sem risco de o modelo distorcer
valores, datas ou nomes. As consultas ganham um campo `display` já pronto; as escritas
são resolvidas por `_format_write_result` (ver agent.py / WRITE_FUNCTIONS).
"""
from datetime import datetime

from ia.tools.categories import CATEGORY_LABELS_PT

RECURRENCE_LABELS_PT = {
    "monthly": "mensal",
    "annual": "anual",
    "weekly": "semanal",
    "only-time": "única",
}

GOAL_PERIOD_LABELS_PT = {
    "weekly": "semanal",
    "monthly": "mensal",
    "quarterly": "trimestral",
    "yearly": "anual",
    "once": "compra única",
}

GOAL_TYPE_LABELS_PT = {
    "c": "compra",
    "e": "economia",
}

MONTHS_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def _brl(value) -> str:
    """4000000.0 -> 'R$ 4.000.000,00'."""
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return f"R$ {value}"


def _fmt_date(value) -> str:
    """datetime ou string ISO -> 'dd/mm/aaaa'. Deixa passar o que não reconhecer."""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).strftime("%d/%m/%Y")
        except ValueError:
            return value
    return str(value)


# ---------------------------------------------------------------------------
# CONSULTAS  ->  campo `display`
# ---------------------------------------------------------------------------

def _expense_line(e: dict) -> str:
    cat = CATEGORY_LABELS_PT.get(e.get("category"), e.get("category"))
    line = f"• {e.get('name')} ({cat}) — {_brl(e.get('value'))}"
    if e.get("date"):
        line += f" — {_fmt_date(e.get('date'))}"
    inst = e.get("installment")
    if inst and inst != "1/1":
        line += f" — parcela {inst}"
    return line


def _income_line(inc: dict) -> str:
    rec = RECURRENCE_LABELS_PT.get(inc.get("recurrence_type"), inc.get("recurrence_type"))
    return f"• {inc.get('name')} — {_brl(inc.get('value'))} ({rec}) — origem: {inc.get('origin')}"


def _goal_line(g: dict) -> str:
    period = GOAL_PERIOD_LABELS_PT.get(g.get("period"), g.get("period"))
    acc = g.get("accumulated_value") or 0
    target = g.get("value") or 0
    pct = f" — {acc / target * 100:.0f}%" if target else ""
    return f"• {g.get('name')} — {_brl(acc)} de {_brl(target)}{pct} ({period})"


def _format_read_result(fn_name: str, result: dict) -> str | None:
    """Texto pronto para uma consulta. Retorna None se não souber formatar
    (ou em erro) — nesse caso o modelo responde a partir do JSON cru."""
    if not isinstance(result, dict) or result.get("status") != "success":
        return None

    if "expenses" in result:
        rows = result["expenses"]
        if fn_name == "get_expenses_by_month":
            header = f"Despesas de {MONTHS_PT.get(result.get('month'), result.get('month'))}:"
        elif fn_name == "get_expenses_by_year":
            header = f"Despesas de {result.get('year')}:"
        elif fn_name == "get_last_month_expenses":
            header = "Despesas do mês passado:"
        elif fn_name == "get_last_month_expenses_by_category":
            header = "Despesas (mês passado):"
        else:
            header = "Despesas:"
        if not rows:
            return f"{header}\nNenhuma despesa encontrada."
        total = sum(r.get("value") or 0 for r in rows)
        body = "\n".join(_expense_line(r) for r in rows)
        return f"{header}\n{body}\n\nTotal: {_brl(total)}"

    if "incomes" in result:
        rows = result["incomes"]
        if not rows:
            return "Nenhuma renda registrada."
        total = sum(r.get("value") or 0 for r in rows)
        body = "\n".join(_income_line(r) for r in rows)
        return f"Rendas:\n{body}\n\nTotal: {_brl(total)}"

    if "income" in result:
        return "Renda:\n" + _income_line(result["income"])

    if "goals" in result:
        rows = result["goals"]
        if not rows:
            return "Nenhuma meta registrada."
        return "Metas:\n" + "\n".join(_goal_line(r) for r in rows)

    if "goal" in result:
        return "Meta:\n" + _goal_line(result["goal"])

    return None


# ---------------------------------------------------------------------------
# ESCRITAS
# ---------------------------------------------------------------------------

def _format_write_result(fn_name: str, fn_args: dict, result: dict) -> str:
    if result.get("status") != "success":
        return f"Erro: {result.get('message', 'falha desconhecida')}"

    if fn_name == "register_expense":
        label = CATEGORY_LABELS_PT.get(fn_args.get("category"), fn_args.get("category"))
        return f"Despesa registrada: {fn_args.get('name')} ({label}) — {_brl(fn_args.get('value'))}"
    if fn_name == "update_expense":
        label = CATEGORY_LABELS_PT.get(fn_args.get("category"), fn_args.get("category"))
        return f"Despesa atualizada: {fn_args.get('name')} ({label}) — {_brl(fn_args.get('value'))}"
    if fn_name == "delete_expense":
        return "Despesa removida com sucesso."

    if fn_name == "register_income":
        return f"Renda registrada: {fn_args.get('name')} — {_brl(fn_args.get('value'))}"
    if fn_name == "update_income":
        return f"Renda atualizada: {fn_args.get('new_name')} — {_brl(fn_args.get('value'))}"
    if fn_name == "delete_income":
        return f"Renda removida: {fn_args.get('income_name')}."

    if fn_name == "register_goal":
        acc = fn_args.get("accumulated_value") or 0
        return (f"Meta registrada: {fn_args.get('name')} — objetivo {_brl(fn_args.get('value'))}, "
                f"já acumulado {_brl(acc)}")
    if fn_name == "update_goal":
        return f"Meta atualizada: {fn_args.get('new_name')} — objetivo {_brl(fn_args.get('value'))}"
    if fn_name == "delete_goal":
        return f"Meta removida: {fn_args.get('goal_name')}."
    if fn_name == "contribute_to_goal":
        accumulated = result.get("accumulated_value")
        target = result.get("target_value")
        return (f"Contribuição registrada em '{fn_args.get('goal_name')}': "
                f"+{_brl(fn_args.get('amount'))} ({_brl(accumulated)} de {_brl(target)})")

    return result.get("message", "Ação concluída com sucesso.")
