import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from tg_bot.configs.bot_settings import API_URL

from dotenv import load_dotenv

load_dotenv()


def create_inline_button(text: str, callback_data: str = None, url: str = None, web_app_url: str = None) -> InlineKeyboardButton:
    """
    Создает кнопку InlineKeyboardButton с указанными параметрами.
    """
    if web_app_url:
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=web_app_url))
    elif url:
        return InlineKeyboardButton(text=text, url=url)
    else:
        return InlineKeyboardButton(text=text, callback_data=callback_data)


button_faq = create_inline_button(text="Вопрос & Ответ", callback_data="faq")
button_payment = create_inline_button(text="Оплатить", callback_data="erip_payment")
button_erip = create_inline_button(text="Оплатить через ЕРИП", callback_data="erip_info")
button_bonuses = create_inline_button(text="Бонусы для клиентов", callback_data="menu_bonuses")
button_manager = create_inline_button(text="Связаться с KLiK", callback_data="contact_manager")
button_tg_links = create_inline_button(text="Ваш чат группы", callback_data="tg_links")
button_links = create_inline_button(text="Будь в тренде!", callback_data="menu_links")
button_trial = create_inline_button(text="Дата пробного занятия", callback_data="user_trial_date")
button_news = create_inline_button(text="Главный новостной канал KLiK", url="https://t.me/KLiK_bel")
button_balance = create_inline_button(text="Баланс", callback_data="check_balance")
button_summer = create_inline_button(text="☀️ Лето с KLiK", callback_data="summer_main")


def get_client_keyboard(user_tg_id) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [button_summer],
            [create_inline_button(text="Личный кабинет KLiKhub", web_app_url=f"{API_URL}webapp/index/?user_tg_id={user_tg_id}&v=1.0.4")] if os.getenv("BOT_DEBUG") == "False" else [],
            [button_balance, button_payment],
            [button_bonuses],
            [button_manager],
            [button_tg_links],
            [button_links],
            [button_faq],
        ]
    )


def get_lead_with_group_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [button_summer],
            [button_balance, button_payment],
            [button_bonuses],
            [button_manager],
            [button_tg_links],
            [button_links],
            [button_faq],
        ]
    )


def get_lead_without_group_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [button_summer],
            [button_faq],
            [button_erip],
            [button_bonuses],
            [button_manager],
            [button_links],
            [button_trial],
            [button_news],
        ]
    )
