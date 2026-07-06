"""Yordamchi funksiyalar: hisobot matnini tayyorlash."""

from html import escape


def build_top_text(top: list[tuple[str, str | None, str | None, int]]) -> str:
    """TOP ro'yxatidan chiroyli matn tuzamiz (HTML formatda)."""
    if not top:
        return "Hali hech kim referal to'plamagan."

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for i, (name, username, phone, count) in enumerate(top, start=1):
        prefix = medals.get(i, f"{i}.")
        safe_name = escape(name)
        username_part = f" (@{escape(username)})" if username else ""
        phone_part = f"\n   📞 +{escape(phone)}" if phone else ""
        lines.append(f"{prefix} {safe_name}{username_part} — <b>{count}</b> ta{phone_part}")

    separator = "\n" + "_" * 40 + "\n"
    return separator.join(lines)