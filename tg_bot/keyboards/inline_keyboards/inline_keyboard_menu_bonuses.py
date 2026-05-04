from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

button_1: InlineKeyboardButton = InlineKeyboardButton(
    text='Партнеры KLiK',
    callback_data='partners_list')

button_2: InlineKeyboardButton = InlineKeyboardButton(
    text='Скидки на обучение',
    callback_data='client_bonuses')

button_3: InlineKeyboardButton = InlineKeyboardButton(
    text='Платформа Lim English',
    callback_data='english_platform')

button_4: InlineKeyboardButton = InlineKeyboardButton(
    text='<< Главное меню',
    callback_data='inline_main_menu')



def get_clients_bonuses_menu_inline_keyboard() -> InlineKeyboardMarkup:
    clients_bonuses_menu_inline: InlineKeyboardMarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                button_1
            ],[
                button_2
            ]
        ]
    )
    return clients_bonuses_menu_inline

def get_clients_bonuses_menu_inline_for_lead_keyboard() -> InlineKeyboardMarkup:
    clients_bonuses_menu_inline_for_lead: InlineKeyboardMarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                button_1
            ],[
                button_2
            ],
        ]
    )
    return clients_bonuses_menu_inline_for_lead