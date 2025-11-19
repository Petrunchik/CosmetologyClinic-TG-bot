import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.handlers import user_router, admin_router
from database.models import async_main
from settings.logging_config import setup_logger


logger = setup_logger("All_errors")


async def on_startup():
    logging.info("Бот запущен!")
    from bot.bot_init import bot
    await bot.send_message(chat_id=..., text="🤖 Бот запущен!")

async def on_shutdown():
    from bot.bot_init import bot
    logging.info("Бот выключается...")
    await bot.send_message(chat_id=..., text="🛑 Бот выключается...")

async def set_commands():
    from bot.bot_init import bot
    commands = [
        BotCommand(command='start', description='🚀Запуск/🔃Обновление')
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def main():

    from bot.bot_init import bot

    await async_main()
    await set_commands()

    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(admin_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())