from tg_bot.handlers.inline_handlers.main_menu import get_user_keyboard
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_bot.service.api_requests import find_user_in_django, get_sales_managers, get_manager, get_user_group_lessons
from tg_bot.configs.bot_messages import *

contact_manager_router = Router()


@contact_manager_router.callback_query(F.data == "contact_manager")
async def get_managers_handler(callback: CallbackQuery):
    """
    Обработчик кнопки "Менеджер".
    """
    telegram_id = str(callback.from_user.id)

    try:
        # Получаем данные пользователя
        user_data = await find_user_in_django(telegram_id)
        if not user_data or not user_data.get("success"):
            await callback.message.answer(MANAGER_ERROR_USER_DATA)
            await callback.answer()
            return

        user = user_data.get("user", {})
        clients = user.get("clients", [])

        if not clients:
            await callback.message.answer(MANAGER_NO_RECORDS)
            await callback.answer()
            return

        # Берем первого клиента для получения информации о менеджере
        for client in clients:
            user_crm_id = client.get("crm_id")
            branch_id = client.get("branch_id")

            if not user_crm_id or not branch_id:
                await callback.message.answer(MANAGER_INSUFFICIENT_DATA)
                await callback.answer()
                return

            # Получаем информацию о менеджере
            manager_info = await get_manager(user_crm_id, branch_id)

            # Создаем клавиатуру для возврата в главное меню
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="« Назад в меню", callback_data="main_menu")

            # Проверяем наличие ответа от API
            if not manager_info:
                await callback.message.answer(MANAGER_ERROR_INFO, reply_markup=keyboard.as_markup())
                await callback.answer()
                return

            # Проверяем успешность запроса
            if not manager_info.get("success"):
                message = manager_info.get("message", "Не удалось получить информацию о менеджере.")

                # Если у клиента нет назначенного менеджера, показываем список всех менеджеров продаж
                if "нет назначенного менеджера" in message or "Менеджер с ID" in message:
                    # Получаем список всех менеджеров продаж
                    sales_managers = await get_sales_managers()

                    if sales_managers and len(sales_managers) > 0:
                        message_text = "ℹ️ У вас нет назначенного менеджера. Вы можете связаться с любым из наших менеджеров:\n\n"

                        for manager in sales_managers:
                            name = manager.get("name", "Не указано")
                            telegram_link = manager.get("telegram_link", "")

                            if telegram_link:
                                message_text += f"👨‍💼 <b>{name}</b>: {telegram_link}\n"
                            else:
                                message_text += f"👨‍💼 <b>{name}</b>\n"

                        await callback.message.answer(message_text, reply_markup=keyboard.as_markup())
                        await callback.answer()
                        return

                # Если другая ошибка или не удалось получить менеджеров
                await callback.message.answer(f"⚠️ {message}", reply_markup=keyboard.as_markup())
                await callback.answer()
                return

            # Проверяем наличие назначенного менеджера
            has_assigned = manager_info.get("has_assigned", False)
            if not has_assigned:
                # Получаем список всех менеджеров продаж
                sales_managers = await get_sales_managers()

                if sales_managers and len(sales_managers) > 0:
                    message_text = MANAGER_NO_ASSIGNED_INTRO

                    for manager in sales_managers:
                        name = manager.get("name", "Не указано")
                        telegram_link = manager.get("telegram_link", "")

                        if telegram_link:
                            message_text += MANAGER_SALES_MANAGER_WITH_TG.format(name=name, telegram_link=telegram_link)
                        else:
                            message_text += MANAGER_SALES_MANAGER_WITHOUT_TG.format(name=name)

                    await callback.message.answer(message_text, reply_markup=keyboard.as_markup())
                    await callback.answer()
                    return
                else:
                    await callback.message.answer(MANAGER_NO_ASSIGNED, reply_markup=keyboard.as_markup())
                    await callback.answer()
                    return

            # Формируем сообщение с информацией о менеджере
            manager_data = manager_info.get("data", {})
            manager_tg = manager_data.get("custom_tg", "")
            manager_name = manager_data.get("name", "Не указано")

            message_text = MANAGER_INFO_TEMPLATE.format(manager_name=manager_name, manager_tg=manager_tg)

            await callback.message.answer(message_text, reply_markup=keyboard.as_markup())
        await callback.answer()

    except Exception as e:
        await callback.message.answer(MANAGER_ERROR_GENERAL)
        await callback.answer()
