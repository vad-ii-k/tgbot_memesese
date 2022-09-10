import asyncio
import logging
from typing import List

from aiogram import Bot
from aiogram import exceptions


async def send_message(bot: Bot, user_id: int | str, text: str, disable_notification: bool = False) -> bool:
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.TelegramForbiddenError:
        logging.error("Target [ID:%s]: got TelegramForbiddenError", user_id)
    except exceptions.TelegramRetryAfter as error:
        logging.error("Target [ID:%s]: Flood limit is exceeded. Sleep %s seconds.", user_id, error.retry_after)
        await asyncio.sleep(error.retry_after)
        return await send_message(bot, user_id, text)  # Recursive call
    except exceptions.TelegramAPIError:
        logging.exception("Target [ID:%s]: failed", user_id)
    else:
        logging.info("Target [ID:%s]: success", user_id)
        return True
    return False


async def broadcast(bot: Bot, users: List[int], text: str) -> int:
    """
    Simple broadcaster
    :return: Count of messages
    """
    count = 0
    try:
        for user_id in users:
            if await send_message(bot, user_id, text):
                count += 1
            await asyncio.sleep(0.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        logging.info("%s/%s messages successful sent.", count, len(users))

    return count
