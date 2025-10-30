from aiogram import Router, F
from aiogram.types import CallbackQuery

from tg_bot.service.api_requests import get_user_balances_from_api
from tg_bot.configs.bot_messages import BALANCE_CHECKING, BALANCE_ERROR, BALANCE_EMPTY, BALANCE_TITLE, \
    BALANCE_CLIENT_TEMPLATE, BALANCE_SUCCESS, BALANCE_CLIENT_NO_NAME

balance_router = Router()


@balance_router.callback_query(F.data == "check_balance")
async def check_balance_handler(callback: CallbackQuery):
    """
    Отправляет балансы всех клиентов пользователя.
    """
    telegram_id = callback.from_user.id

    # Уведомляем пользователя о начале проверки баланса
    await callback.message.answer(BALANCE_CHECKING)

    # Получаем балансы клиентов через API
    balances = await get_user_balances_from_api(telegram_id)
    print(balances)
    if not balances:
        await callback.message.answer(BALANCE_ERROR)
        await callback.answer()
        return

    # Если балансы пустые
    if not balances:
        await callback.message.answer(BALANCE_EMPTY)
        await callback.answer()
        return

    # Формируем текст сообщения с балансами
    balance_message = BALANCE_TITLE
    for client in balances:
        client_name = client.get("client_name", BALANCE_CLIENT_NO_NAME)
        balance = client.get("balance", 0.0)
        try:
            balance = float(balance)
        except (ValueError, TypeError):
            balance = 0.0
        balance_message += BALANCE_CLIENT_TEMPLATE.format(client_name=client_name, balance=balance)

    # Отправляем сообщение с балансами
    await callback.message.answer(balance_message, parse_mode="HTML")
    await callback.answer(BALANCE_SUCCESS)
