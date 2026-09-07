"""
Роутер для сценария «Лето с KLiK».
Обрабатывает inline-кнопки: summer_main, summer_away, summer_city_{id}, summer_format_{id}.
"""

from urllib.parse import urlparse

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_bot.configs.bot_settings import API_URL, SUMMER_FEATURE_ENABLED
from tg_bot.configs.bot_messages import (
    SUMMER_SELECT_DIRECTION,
    SUMMER_CITY_SELECT_FORMAT,
    SUMMER_DATA_ERROR,
    SUMMER_NO_FORMATS,
    SUMMER_FEATURE_DISABLED,
)
from tg_bot.service.api_requests import get_summer_data, track_summer_click
from tg_bot.service.manager_service import send_manager_contacts
from tg_bot.configs.logger_config import get_logger

logger = get_logger()

summer_camp_router = Router()


if not SUMMER_FEATURE_ENABLED:

    @summer_camp_router.callback_query(F.data.startswith("summer_"))
    async def handle_summer_disabled(callback: CallbackQuery):
        """
        Заглушка на время, пока раздел «Лето с KLiK» скрыт.

        Кнопки в меню больше нет, но она осталась в старых сообщениях чата,
        и её по-прежнему можно нажать. Обработчик зарегистрирован первым,
        поэтому перехватывает все callback-и раздела и дальше по сценарию
        не пускает. Когда SUMMER_FEATURE_ENABLED = True, заглушка не
        создаётся и раздел работает как раньше.
        """
        await callback.answer(SUMMER_FEATURE_DISABLED, show_alert=True)


def _build_full_image_url(image_url: str) -> str:
    """Собирает полный URL изображения из относительного пути."""
    parsed = urlparse(image_url)
    if not parsed.scheme:
        return API_URL.rstrip("/") + "/" + image_url.lstrip("/")
    return image_url


@summer_camp_router.callback_query(F.data == "summer_main")
async def handle_summer_main(callback: CallbackQuery):
    """
    Главная кнопка «☀️ Лето с KLiK».
    Показывает меню направлений: Выездной лагерь + Города.
    """
    # Трекаем клик
    await track_summer_click("main")

    # Получаем данные из API
    data = await get_summer_data()
    if not data:
        await callback.answer(SUMMER_DATA_ERROR, show_alert=True)
        return

    # Проверяем активность фичи
    if not data.get("is_active", True):
        await callback.answer(SUMMER_FEATURE_DISABLED, show_alert=True)
        return

    # Строим клавиатуру
    keyboard = InlineKeyboardBuilder()

    # Кнопка «Выездной лагерь» (если есть текст)
    away_camp = data.get("away_camp", {})
    if away_camp.get("text"):
        keyboard.button(text="🏕 Выездной лагерь", callback_data="summer_away")

    # Кнопки городов
    cities = data.get("cities", [])
    for city in cities:
        keyboard.button(
            text=f"📍 {city['name']}",
            callback_data=f"summer_city_{city['id']}"
        )

    keyboard.button(text="« Назад в меню", callback_data="inline_main_menu")
    keyboard.adjust(1)

    # Отправляем / редактируем сообщение
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            SUMMER_SELECT_DIRECTION, reply_markup=keyboard.as_markup()
        )
    else:
        await callback.message.edit_text(
            SUMMER_SELECT_DIRECTION, reply_markup=keyboard.as_markup()
        )
    await callback.answer()


@summer_camp_router.callback_query(F.data == "summer_away")
async def handle_summer_away(callback: CallbackQuery):
    """
    Выездной лагерь — отправка текста + фото + контакты менеджера.
    """
    # Трекаем клик
    await track_summer_click("away")

    data = await get_summer_data()
    if not data:
        await callback.answer(SUMMER_DATA_ERROR, show_alert=True)
        return

    away_camp = data.get("away_camp", {})
    text = away_camp.get("text", "")
    image_url = away_camp.get("image")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="« Назад", callback_data="summer_main")
    keyboard.adjust(1)

    # Отправляем контент
    await _send_content(callback, text, image_url, keyboard)

    # Отправляем контакты менеджера отдельным сообщением
    telegram_id = str(callback.from_user.id)
    await send_manager_contacts(callback.message, telegram_id)

    await callback.answer()


@summer_camp_router.callback_query(F.data.startswith("summer_city_"))
async def handle_summer_city(callback: CallbackQuery):
    """
    Выбор города — показ кнопок форматов.
    """
    city_id_str = callback.data.split("_")[-1]
    try:
        city_id = int(city_id_str)
    except ValueError:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    # Трекаем клик
    await track_summer_click("city", city_id)

    data = await get_summer_data()
    if not data:
        await callback.answer(SUMMER_DATA_ERROR, show_alert=True)
        return

    # Ищем город в данных
    cities = data.get("cities", [])
    city = None
    for c in cities:
        if c["id"] == city_id:
            city = c
            break

    if not city:
        await callback.answer("Город не найден.", show_alert=True)
        return

    formats = city.get("formats", [])
    if not formats:
        await callback.answer(SUMMER_NO_FORMATS, show_alert=True)
        return

    # Строим клавиатуру с форматами
    keyboard = InlineKeyboardBuilder()
    for fmt in formats:
        keyboard.button(
            text=fmt["button_name"],
            callback_data=f"summer_format_{fmt['id']}"
        )
    keyboard.button(text="« Назад", callback_data="summer_main")
    keyboard.adjust(1)

    city_name = city["name"]
    text = SUMMER_CITY_SELECT_FORMAT.format(city_name=city_name)

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard.as_markup())
    else:
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback.answer()


@summer_camp_router.callback_query(F.data.startswith("summer_format_"))
async def handle_summer_format(callback: CallbackQuery):
    """
    Выбор формата — отправка текста + фото + контакты менеджера.
    """
    format_id_str = callback.data.split("_")[-1]
    try:
        format_id = int(format_id_str)
    except ValueError:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    # Трекаем клик
    await track_summer_click("format", format_id)

    data = await get_summer_data()
    if not data:
        await callback.answer(SUMMER_DATA_ERROR, show_alert=True)
        return

    # Ищем формат среди всех городов
    target_format = None
    parent_city_id = None
    for city in data.get("cities", []):
        for fmt in city.get("formats", []):
            if fmt["id"] == format_id:
                target_format = fmt
                parent_city_id = city["id"]
                break
        if target_format:
            break

    if not target_format:
        await callback.answer("Формат не найден.", show_alert=True)
        return

    text = target_format.get("text", "")
    image_url = target_format.get("image")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="« Назад", callback_data=f"summer_city_{parent_city_id}")
    keyboard.adjust(1)

    # Отправляем контент
    await _send_content(callback, text, image_url, keyboard)

    # Отправляем контакты менеджера отдельным сообщением
    telegram_id = str(callback.from_user.id)
    await send_manager_contacts(callback.message, telegram_id)

    await callback.answer()


async def _send_content(
    callback: CallbackQuery,
    text: str,
    image_url: str | None,
    keyboard: InlineKeyboardBuilder,
) -> None:
    """
    Вспомогательная функция для отправки контента (текст + опциональное фото).
    Обеспечивает атомарность операций и безопасный fallback при ошибках Telegram API.
    """
    if image_url:
        full_url = _build_full_image_url(image_url)
        try:
            if callback.message.photo:
                # Редактируем существующее медиа-сообщение
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=full_url, caption=text),
                    reply_markup=keyboard.as_markup(),
                )
            else:
                # Пытаемся отправить фото ПЕРЕД удалением текстового сообщения
                await callback.message.answer_photo(
                    photo=full_url,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                )
                # Если отправка фото успешна — удаляем старое текстовое сообщение
                try:
                    await callback.message.delete()
                except Exception as del_err:
                    logger.warning(f"Не удалось удалить старое сообщение: {del_err}")
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            # Fallback — оставляем/отправляем только текст
            if callback.message.photo:
                # Если редактирование медиа упало, удаляем его и шлем текст заново
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(
                    text, reply_markup=keyboard.as_markup()
                )
            else:
                # Если отправка фото упала, старое текстовое сообщение НЕ удалено (см. try выше)
                # Просто редактируем его текст
                await callback.message.edit_text(
                    text, reply_markup=keyboard.as_markup()
                )
    else:
        # Нет изображения — только текст
        if callback.message.photo:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(text, reply_markup=keyboard.as_markup())
        else:
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup())

