from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_bot.service.manager_service import send_manager_contacts

contact_manager_router = Router()


@contact_manager_router.callback_query(F.data == "contact_manager")
async def get_managers_handler(callback: CallbackQuery):
    """
    Обработчик кнопки "Менеджер".
    Делегирует логику в manager_service.send_manager_contacts.
    """
    telegram_id = str(callback.from_user.id)

    # Кнопка «Назад в меню» добавляется отдельно после ответа сервиса
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="« Назад в меню", callback_data="main_menu")

    await send_manager_contacts(callback.message, telegram_id, reply_markup=keyboard.as_markup())
    await callback.answer()

