from tg_bot.handlers.inline_handlers.main_menu import get_user_keyboard
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from urllib.parse import urlparse
from tg_bot.configs.bot_settings import API_URL

from tg_bot.service.api_requests import (
    find_user_in_django,
    get_partner_by_id,
    get_partner_categories,
    get_partner_cities,
    get_partners_filtered,
)
from tg_bot.configs.bot_messages import (
    PARTNER_NOT_FOUND,
    PARTNER_INFO_RESIDENTS_ONLY,
    PARTNER_INFO_TEMPLATE,
    PARTNER_INFO_WITH_CODE_TEMPLATE,
    PARTNER_CATEGORIES_EMPTY,
    PARTNER_SELECT_CATEGORY,
    PARTNER_LIST_EMPTY,
    PARTNER_SELECT,
)


partners_router = Router()


@partners_router.callback_query(F.data == "partners_list")
async def partners_handler(callback: CallbackQuery):
    """
    Обработчик кнопки "Партнеры".
    Отправляет список городов.
    """
    cities = await get_partner_cities()
    if not cities:
        await callback.message.answer("Список городов пуст.")
        await callback.answer()
        return

    # Создаем клавиатуру с городами
    keyboard = InlineKeyboardBuilder()
    for city in cities:
        keyboard.button(text=city["name"], callback_data=f"partner_city_{city['id']}")
    keyboard.button(text="<< Назад", callback_data="inline_main_menu")
    keyboard.adjust(1)

    await callback.message.edit_text("Выберите город:", reply_markup=keyboard.as_markup())
    await callback.answer()


@partners_router.callback_query(F.data.startswith("partner_city_"))
async def handle_city_selection(callback: CallbackQuery):
    """
    Обработчик выбора города.
    Отправляет список категорий.
    """
    city_id = callback.data.split("_")[-1]
    categories = await get_partner_categories()

    if not categories:
        await callback.message.answer(PARTNER_CATEGORIES_EMPTY)
        await callback.answer()
        return

    # Создаем клавиатуру с категориями
    keyboard = InlineKeyboardBuilder()
    for category in categories:
        # Передаем city_id и category_id
        keyboard.button(text=category["name"], callback_data=f"partner_select_{city_id}_{category['id']}")
    
    keyboard.button(text="<< Назад", callback_data="partners_list")
    keyboard.adjust(1)

    await callback.message.edit_text(PARTNER_SELECT_CATEGORY, reply_markup=keyboard.as_markup())
    await callback.answer()


@partners_router.callback_query(F.data.startswith("partner_select_"))
async def handle_category_selection(callback: CallbackQuery):
    """
    Обработчик выбора категории (с учетом города).
    Отправляет список партнеров и их бонусов.
    """
    # callback: partner_select_{city_id}_{category_id}
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("Ошибка данных", show_alert=True)
        return
        
    city_id = parts[2]
    category_id = parts[3]
    
    partners = await get_partners_filtered(city_id, category_id)
    if not partners:
        await callback.answer("В данном городе нет партнеров этой категории", show_alert=True)
        return

    # Создаем клавиатуру с партнерами
    keyboard = InlineKeyboardBuilder()
    for partner in partners:
        # Передаем partner_id и city_id для корректного возврата
        keyboard.button(text=partner["partner_name"], callback_data=f"partner_info_{partner['id']}_{city_id}")
    
    keyboard.button(text="Назад", callback_data=f"partner_city_{city_id}")
    keyboard.adjust(1)

    await callback.message.edit_text(PARTNER_SELECT, reply_markup=keyboard.as_markup())
    await callback.answer()


@partners_router.callback_query(F.data.startswith("partner_info_"))
async def handle_partner_selection(callback: CallbackQuery):
    """
    Обработчик выбора партнера.
    Отправляет информацию о бонусах и изображение партнера.
    """
    # callback: partner_info_{partner_id}_{city_id}
    parts = callback.data.split("_")
    partner_id = parts[2]
    city_id = parts[3] if len(parts) > 3 else None
    
    partner = await get_partner_by_id(partner_id)
    if not partner:
        await callback.message.answer(PARTNER_NOT_FOUND)
        await callback.answer()
        return

    # Проверяем статус пользователя
    user_status = await get_user_status(str(callback.from_user.id))

    if user_status == "2":
        # Проверяем наличие промо-кода
        if partner.get("code"):
            formatted_text = PARTNER_INFO_WITH_CODE_TEMPLATE.format(partner_name=partner["partner_name"], partner_description=partner["description"], partner_code=partner["code"])
        else:
            formatted_text = PARTNER_INFO_TEMPLATE.format(partner_name=partner["partner_name"], partner_description=partner["description"])
    else:
        formatted_text = PARTNER_INFO_RESIDENTS_ONLY

    keyboard = InlineKeyboardBuilder()
    
    # Кнопка Назад должна вести к списку партнеров (Category select view)
    # Нам нужен city_id и category_id. category_id берем из партнера.
    if city_id and partner.get('category'):
        keyboard.button(text="<< Назад", callback_data=f"partner_select_{city_id}_{partner['category']}")
    else:
        # Fallback если данных не хватает
        keyboard.button(text="<< Назад", callback_data="partners_list")
        
    keyboard.adjust(1)

    # Проверяем наличие изображения и отправляем его с текстом или только текст
    image_url = partner.get("image")
    if image_url:
        # Проверяем, является ли URL относительным (не содержит http/https)
        parsed_url = urlparse(image_url)

        if not parsed_url.scheme:  # Если схема отсутствует, значит URL относительный
            # Составляем полный URL, объединив с базовым URL API
            full_image_url = API_URL.rstrip("/") + "/" + image_url.lstrip("/")
            image_url = full_image_url

        # Отправляем медиа с описанием
        try:
            await callback.message.edit_media(media=InputMediaPhoto(media=image_url, caption=formatted_text), reply_markup=keyboard.as_markup())
        except Exception as e:
            # Если не удалось загрузить изображение, отправляем только текст
            await callback.message.edit_text(formatted_text, reply_markup=keyboard.as_markup())
    else:
        # Если изображения нет, отправляем обычный текст
        await callback.message.edit_text(formatted_text, reply_markup=keyboard.as_markup())

    await callback.answer()


async def get_user_status(telegram_id: str) -> str:
    """
    Получает статус пользователя из базы данных Django.
    """
    user_data = await find_user_in_django(telegram_id)
    if user_data and user_data.get("success"):
        user = user_data.get("user", {})
        return user.get("status", "0")
    return "0"
