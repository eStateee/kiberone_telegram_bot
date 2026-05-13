"""
Сервис для отправки контактов менеджера пользователю.
Извлечённая логика из kiberone_manager.py для переиспользования
в других сценариях (Лето с KLiK и т.д.).
"""

from aiogram.types import Message, InlineKeyboardMarkup

from tg_bot.service.api_requests import find_user_in_django, get_sales_managers, get_manager
from tg_bot.configs.bot_messages import (
    MANAGER_ERROR_USER_DATA,
    MANAGER_NO_RECORDS,
    MANAGER_INSUFFICIENT_DATA,
    MANAGER_ERROR_INFO,
    MANAGER_NO_ASSIGNED_INTRO,
    MANAGER_NO_ASSIGNED,
    MANAGER_ERROR_GENERAL,
    MANAGER_INFO_TEMPLATE,
    MANAGER_SALES_MANAGER_WITH_TG,
    MANAGER_SALES_MANAGER_WITHOUT_TG,
)
from tg_bot.configs.logger_config import get_logger

logger = get_logger()


async def send_manager_contacts(message: Message, telegram_id: str, reply_markup: InlineKeyboardMarkup = None) -> None:
    """
    Отправляет контакты менеджера отдельным сообщением.
    
    Логика:
    1. Получить данные пользователя из Django
    2. Для каждого клиента получить менеджера из CRM
    3. Если менеджер назначен — отправить его данные
    4. Если нет — отправить список дежурных менеджеров (SalesManagers)
    """
    try:
        # Получаем данные пользователя
        user_data = await find_user_in_django(telegram_id)
        if not user_data or not user_data.get("success"):
            await message.answer(MANAGER_ERROR_USER_DATA, reply_markup=reply_markup)
            return

        user = user_data.get("user", {})
        clients = user.get("clients", [])

        if not clients:
            # Нет записей в CRM — показываем дежурных менеджеров
            await _send_sales_managers_fallback(message, reply_markup)
            return

        # Берем первого клиента для получения информации о менеджере
        for client in clients:
            user_crm_id = client.get("crm_id")
            branch_id = client.get("branch_id")

            if not user_crm_id or not branch_id:
                continue

            # Получаем информацию о менеджере
            manager_info = await get_manager(user_crm_id, branch_id)

            # Проверяем наличие ответа от API
            if not manager_info:
                await message.answer(MANAGER_ERROR_INFO, reply_markup=reply_markup)
                return

            # Проверяем успешность запроса
            if not manager_info.get("success"):
                mgr_message = manager_info.get("message", "")
                # Если у клиента нет назначенного менеджера — показываем дежурных
                if "нет назначенного менеджера" in mgr_message or "Менеджер с ID" in mgr_message:
                    await _send_sales_managers_fallback(message, reply_markup)
                    return
                await message.answer(f"⚠️ {mgr_message}", reply_markup=reply_markup)
                return

            # Проверяем наличие назначенного менеджера
            has_assigned = manager_info.get("has_assigned", False)
            if not has_assigned:
                await _send_sales_managers_fallback(message, reply_markup)
                return

            # Формируем сообщение с информацией о менеджере
            manager_data = manager_info.get("data", {})
            manager_tg = manager_data.get("custom_tg", "")
            manager_name = manager_data.get("name", "Не указано")

            message_text = MANAGER_INFO_TEMPLATE.format(
                manager_name=manager_name, manager_tg=manager_tg
            )
            await message.answer(message_text, reply_markup=reply_markup)
            return

        # Если ни один клиент не подошёл — дежурные менеджеры
        await _send_sales_managers_fallback(message, reply_markup)

    except Exception as e:
        logger.error(f"Ошибка при отправке контактов менеджера: {e}")
        await message.answer(MANAGER_ERROR_GENERAL, reply_markup=reply_markup)


async def _send_sales_managers_fallback(message: Message, reply_markup: InlineKeyboardMarkup = None) -> None:
    """Отправляет список дежурных менеджеров (fallback)."""
    sales_managers = await get_sales_managers()

    if sales_managers and len(sales_managers) > 0:
        message_text = MANAGER_NO_ASSIGNED_INTRO

        for manager in sales_managers:
            name = manager.get("name", "Не указано")
            telegram_link = manager.get("telegram_link", "")

            if telegram_link:
                message_text += MANAGER_SALES_MANAGER_WITH_TG.format(
                    name=name, telegram_link=telegram_link
                )
            else:
                message_text += MANAGER_SALES_MANAGER_WITHOUT_TG.format(name=name)

        await message.answer(message_text, reply_markup=reply_markup)
    else:
        await message.answer(MANAGER_NO_ASSIGNED, reply_markup=reply_markup)
