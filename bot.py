import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from tg_bot.configs.bot_settings import BOT_TOKEN
from tg_bot.handlers import handler_start
from tg_bot.configs.set_commands import set_main_menu
from tg_bot.configs.logger_config import get_logger
from tg_bot.handlers.inline_handlers.check_balance import balance_router
from tg_bot.handlers.inline_handlers.inline_handler_english_platform import english_platform_router

from tg_bot.handlers.inline_handlers.main_menu import main_menu_router
from tg_bot.handlers.inline_handlers.faq import faq_router
from tg_bot.handlers.inline_handlers.erip import erip_router
from tg_bot.handlers.inline_handlers.menu_bonuses import menu_bonuses_router
from tg_bot.handlers.inline_handlers.partner import partners_router
from tg_bot.handlers.inline_handlers.bonus import bonuses_router
from tg_bot.handlers.inline_handlers.kiberone_manager import contact_manager_router
from tg_bot.handlers.inline_handlers.social_links import social_router
from tg_bot.handlers.inline_handlers.trial_lesson import trial_lesson_router
from tg_bot.handlers.inline_handlers.summer_camp import summer_camp_router


logger = get_logger()


async def on_startup(bot: Bot):
    logger.info("Starting bot..")
    # await bot.send_message(chat_id="404331105", text="Bot started!")


async def on_shutdown(bot: Bot):
    logger.info("Processing shutdown..")

async def main():
    """
    Main function of the bot.

    Initialize bot and dispatcher, register startup and shutdown callbacks,
    include routers, delete webhook, set main menu, start polling and close bot session.

    :return: None
    """
    bot: Bot = Bot(
        token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp: Dispatcher = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_routers (
        handler_start.start_router,
        main_menu_router,
        summer_camp_router,
        faq_router,
        erip_router,
        partners_router,
        bonuses_router,
        contact_manager_router,
        social_router,
        trial_lesson_router,
        balance_router,
        menu_bonuses_router,
        english_platform_router,
    )

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await set_main_menu(bot)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), timeout_seconds=30, polling_timeout=30)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
