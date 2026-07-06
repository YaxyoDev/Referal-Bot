"""Throttling middleware: har bir foydalanuvchidan 1 soniyada 1 xabar o'tkazamiz."""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """
    Spamdan himoya. Har bir foydalanuvchidan belgilangan vaqt (default 1 soniya)
    ichida faqat 1 ta xabar handlerga o'tadi. Qolganlari jim tashlanadi.
    """

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit  # Xabarlar orasidagi minimal vaqt (soniya)
        self._last_time: dict[int, float] = {}  # user_id -> oxirgi xabar vaqti

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user is not None:
            now = time.monotonic()
            last = self._last_time.get(user.id, 0.0)

            # Oldingi xabardan 1 soniya o'tmagan bo'lsa — o'tkazmaymiz
            if now - last < self.rate_limit:
                return None

            self._last_time[user.id] = now

        # Vaqt yetarli o'tgan — xabarni handlerga uzatamiz
        return await handler(event, data)
