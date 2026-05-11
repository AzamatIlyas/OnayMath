from __future__ import annotations

from typing import Any

import httpx

from app.core.settings import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _build_messages(message: str, topic_title: str | None, history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    system_prompt = (
        "Сен OnayMath платформасының мектеп математикасы бойынша AI-көмекшісісің. "
        "Жауаптарды қазақ тілінде, оқушыға түсінікті қысқа қадамдармен бер. "
        "Формуланы қолдансаң, неге сол формула алынғанын да түсіндір."
    )
    if topic_title:
        system_prompt += f" Ағымдағы тақырып: {topic_title}."

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if history:
        for item in history[-10:]:
            role = item.get("role", "").strip().lower()
            if role not in {"user", "assistant"}:
                continue
            content = (item.get("content") or "").strip()
            if not content:
                continue
            messages.append({"role": role, "content": content[:2000]})

    messages.append({"role": "user", "content": message})
    return messages


async def generate_groq_response(
    message: str,
    topic_title: str | None,
    history: list[dict[str, str]] | None = None,
) -> str | None:
    if not settings.GROQ_ENABLED:
        return None

    payload: dict[str, Any] = {
        "model": settings.GROQ_MODEL,
        "messages": _build_messages(message, topic_title, history),
        "temperature": 0.2,
        "max_tokens": 700,
    }

    headers = {
        "authorization": f"Bearer {settings.GROQ_API_TOKEN}",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            response = await client.post(GROQ_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return None

    choices = data.get("choices") or []
    if not choices:
        return None

    content = (((choices[0] or {}).get("message") or {}).get("content") or "").strip()
    return content or None
