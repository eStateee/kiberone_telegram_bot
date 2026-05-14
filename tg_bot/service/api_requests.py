# -----------------------------------------------------------
import asyncio

# ОТПРАВКА ЗАПРОСОВ НА АПИ

# -----------------------------------------------------------

import aiohttp
from aiogram.types import Message

from tg_bot.configs.bot_settings import API_URL
from tg_bot.configs.logger_config import get_logger

from tg_bot.configs.logger_config import get_logger

logger = get_logger()


async def get_partner_cities() -> list | None:
    """
    Получение списка городов партнеров.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_partner_cities/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении городов: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении городов: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_partners_filtered(city_id: int, category_id: int) -> list | None:
    """
    Получение списка партнеров по городу и категории.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_partners_filtered/{city_id}/{category_id}/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении партнеров: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении партнеров: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def find_user_in_django(telegram_id: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            data = {"telegram_id": telegram_id}
            async with session.post(
                    f"{API_URL}api/find_user_in_db/",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=5)  # добавляем таймаут
            ) as response:
                response_data = await response.json()

                # Успешный ответ от API (независимо от статуса)
                if response_data.get("success", False):
                    user = response_data.get("user", {})
                    if not user:
                        logger.error(f"API вернул success=True, но без данных пользователя")
                        return {"success": False, "message": "Ошибка данных пользователя"}

                    try:
                        user_id = user["id"]
                        clients = await get_clients_by_user(user_id)
                        user["clients"] = clients or []
                        logger.info(f"Найден пользователь и {len(clients)} клиентов")
                        return {"success": True, "user": user}
                    except KeyError:
                        logger.error("В ответе API отсутствует user.id")
                        return {"success": False, "message": "Ошибка данных пользователя"}

                # Пользователь не найден (но API ответило корректно)
                return {
                    "success": False,
                    "message": response_data.get("message", "Пользователь не найден")
                }

    except asyncio.TimeoutError:
        logger.error(f"Таймаут при запросе к API для telegram_id {telegram_id}")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка соединения с API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запросе к API: {str(e)}")
        return None


async def get_clients_by_user(user_id: int) -> list | None:
    """
    Получение списка клиентов для указанного пользователя.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_clients_by_user/{user_id}/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(
                            f"Клиенты для пользователя {user_id} успешно получены."
                        )
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении клиентов: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении клиентов: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def register_user_in_db(telegram_id: str, username: str, phone_number: str) -> dict | None:
    url = f"{API_URL}api/register_user_in_db/"
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "phone_number": phone_number,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status in [200, 201]:
                    response_data = await response.json()
                    if response_data.get("success") and "user" in response_data:
                        logger.info(
                            "Пользователь успешно зарегистрирован в базе данных Django."
                        )
                        return response_data
                    else:
                        logger.error(
                            f"Ошибка регистрации пользователя: {response_data.get('message')}"
                        )
                        return None
                else:
                    error_message = (await response.json()).get(
                        "message", "Неизвестная ошибка"
                    )
                    logger.error(f"Ошибка регистрации пользователя: {error_message}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к Django: {e}")
        return {"success": False, "error": str(e)}


async def find_user_in_crm(phone_number) -> dict | None:
    """
    Поиск пользователя в CRM. Функция посредник, для вызова API.
    """
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}api/find_user_in_crm/"
        data = {"phone_number": phone_number}
        async with session.post(url, json=data) as response:
            response_data: dict = await response.json()
            return response_data.get("user", None)


async def register_user_in_crm(message: Message, phone_number: str) -> dict | None:
    tg_user = message.from_user
    user_data = {
        "first_name": tg_user.first_name or "",
        "last_name": tg_user.last_name or "",
        "username": tg_user.username,
        "phone_number": phone_number,
        # TODO: Добавить выбор города/филиала в боте перед регистрацией (Этап 3)
        # В настоящее время backend (crm_service.py) хардкодит "branch_ids": 1. 
        # Нужно отправлять 'branch_id' отсюда после опроса пользователя.
    }
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}api/register_user_in_crm/"
        async with session.post(url, json=user_data) as response:
            response_data: dict = await response.json()
            return response_data.get("data", None)


async def create_or_update_clients_from_crm(db_user, crm_items: list) -> dict | None:
    """
    Отправляет данные на API для создания, обновления или удаления клиентов.
    """
    url = f"{API_URL}api/create_or_update_clients_in_db/"
    data = {
        "user_id": db_user["id"],
        "crm_items": crm_items,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                response_data: dict = await response.json()

                if not response_data.get("success"):
                    logger.info(
                        f"Ошибка при обновлении клиентов: {response_data.get('message')}"
                    )
                    return None
                else:
                    logger.info("Клиенты успешно обновлены в базе данных Django.")
                    return response_data
            else:
                error_message = (await response.json()).get(
                    "message", "Неизвестная ошибка"
                )
                logger.error(f"Ошибка при обновлении клиентов: {error_message}")
                return None


async def get_all_questions() -> list | None:
    """
    Получает список всех вопросов из API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}api/questions/") as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении вопросов: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении вопросов: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_sales_managers() -> list | None:
    """
    Получает список всех менеджеров продаж из API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}api/get_sales_managers/") as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(f"Список менеджеров продаж успешно получен.")
                        return response_data.get("data", [])
                    else:
                        logger.error(f"Ошибка при получении менеджеров продаж: {response_data.get('message')}")
                        return None
                else:
                    logger.error(f"Не удалось выполнить запрос к API: {response.status}, message='{await response.text()}', url='{response.url}'")
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_answer_by_question_id(question_id: int) -> dict | None:
    """
    Получает ответ на вопрос по ID из API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/answer_by_question/{question_id}/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Ошибка при получении ответа: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении ответа: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_erip_payment_help() -> dict | None:
    """
    Запрос инструкции по оплате через ЕРИП.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_erip_payment_help/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Инструкция не найдена: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении инструкции: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_partner_categories() -> list | None:
    """
    Получение списка всех категорий партнеров.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_partner_categories/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info("Категории партнеров успешно получены.")
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении категорий: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении категорий: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_partners_by_category(category_id: int) -> list | None:
    """
    Получение списка партнеров и их бонусов по ID категории.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_partners_by_category/{category_id}/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(
                            f"Партнеры категории {category_id} успешно получены."
                        )
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении партнеров: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении партнеров: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_partner_by_id(partner_id: int) -> dict | None:
    """
    Получение информации о партнере по его ID.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_partner_by_id/{partner_id}/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(
                            f"Информация о партнере {partner_id} успешно получена."
                        )
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Ошибка при получении партнера: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении партнера: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_client_bonuses() -> list | None:
    """
    Получение списка всех бонусов для клиентов.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_client_bonuses/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info("Бонусы успешно получены.")
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении бонусов: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении бонусов: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_bonus_by_id(bonus_id: str) -> dict | None:
    """
    Получение информации о бонусе по его ID.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_bonus_by_id/{bonus_id}/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(f"Информация о бонусе {bonus_id} успешно получена.")
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Ошибка при получении бонуса: {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении бонуса: {await response.json()}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None



async def get_social_links_from_api() -> list | None:
    """
    Получение списка социальных ссылок через API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/get_social_links/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info("Социальные ссылки успешно получены.")
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении социальных ссылок: {response_data.get('message')}"
                        )
                        return None
                else:
                    error_details = await response.json()
                    logger.error(
                        f"Ошибка при получении социальных ссылок: {error_details}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_user_trial_lessons(user_crm_id: int, branch_id: int) -> dict | None:
    """
    Получение пробных уроков пользователя через API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "user_crm_id": user_crm_id,
                "branch_id": branch_id,
                "lesson_status": 1,  # Запланированные уроки
                "lesson_type": 3,  # Пробные уроки
            }
            async with session.post(
                f"{API_URL}api/get_user_lessons/", json=data
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(
                            f"Пробные уроки успешно получены для user_crm_id={user_crm_id}"
                        )
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Ошибка при получении пробных уроков: {response_data.get('message')}"
                        )
                        return None
                else:
                    error_details = await response.json()
                    logger.error(
                        f"Ошибка при получении пробных уроков: {error_details}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_user_group_lessons(user_crm_id: int, branch_id: int) -> dict | None:
    """
    Получение пробных уроков пользователя через API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "user_crm_id": user_crm_id,
                "branch_id": branch_id,
                "lesson_status": 1,  # Запланированные уроки
                "lesson_type": 2,  # Пробные уроки
            }
            async with session.post(
                f"{API_URL}api/get_user_lessons/", json=data
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(
                            f"Пробные уроки успешно получены для user_crm_id={user_crm_id}"
                        )
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Ошибка при получении пробных уроков: {response_data.get('message')}"
                        )
                        return None
                else:
                    error_details = await response.json()
                    logger.error(
                        f"Ошибка при получении пробных уроков: {error_details}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_location_info(location_id: int) -> dict | None:
    """
    Получение информации о локации через API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}api/get_location_by_id/{location_id}/"
            async with session.get(url) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(
                            f"Локация с room_id={location_id} успешно получена."
                        )
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Ошибка при получении локации: {response_data.get('message')}"
                        )
                        return None
                else:
                    error_details = await response.json()
                    logger.error(f"Ошибка при получении локации: {error_details}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_manager(user_crm_id: int, branch_id: int) -> dict | None:
    """
    Получение информации о менеджере клиента через API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}api/get_manager/{branch_id}/{user_crm_id}/"
            async with session.get(url) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(f"Информация о менеджере для user_crm_id={user_crm_id} успешно получена.")
                        return response_data
                    else:
                        logger.info(f"Менеджер не найден для user_crm_id={user_crm_id}: {response_data.get('message')}")
                        return response_data  # Возвращаем данные даже при success=False
                else:
                    error_details = await response.json()
                    logger.error(f"Ошибка при получении информации о менеджере: {error_details}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_user_balances_from_api(telegram_id: int) -> dict | None:
    """
    Получение баланса клиентов пользователя через API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            data = {"telegram_id": telegram_id}
            url = f"{API_URL}api/get_user_balances/"
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(
                            f"Балансы для telegram_id={telegram_id} успешно получены."
                        )
                        return response_data.get("data", [])
                    else:
                        logger.error(
                            f"Ошибка при получении балансов: {response_data.get('message')}"
                        )
                        return None
                else:
                    error_details = await response.json()
                    logger.error(f"Ошибка при получении балансов: {error_details}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_payment_data_from_api(telegram_id: int) -> list | None:
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}api/get_client_payment_data/"
            data = {"user_id": telegram_id}
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        return response_data.get("data", [])
                    else:
                        logger.error(f"Ошибка при расчете платежей: {response_data.get('message')}")
                        return None
                else:
                    error_details = await response.json()
                    logger.error(f"Ошибка при расчете платежей: {error_details}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_user_tg_links_from_api(telegram_id: str) -> list | None:
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}api/get_user_tg_links/"
            data = {"user_id": telegram_id}
            async with session.get(url, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info(f"Телеграм ссылки успешно получены")
                        return response_data.get("data", [])
                    else:
                        logger.error(f"Ошибка при получении телеграм ссылок {response_data.get('message')}")
                        return None
                else:
                    error_details = await response.json()
                    logger.error(f"Ошибка при получении телеграм ссылок: {error_details}")
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API: {e}")
        return None


async def get_summer_data() -> dict | None:
    """
    Получение структуры летних лагерей из API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}api/summer/data/"
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        logger.info("Данные 'Лето с KLiK' успешно получены.")
                        return response_data.get("data", {})
                    else:
                        logger.error(
                            f"Ошибка при получении данных 'Лето с KLiK': {response_data.get('message')}"
                        )
                        return None
                else:
                    logger.error(
                        f"Ошибка при получении данных 'Лето с KLiK': status={response.status}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API (summer/data): {e}")
        return None


async def track_summer_click(entity_type: str, entity_id: int = 0) -> bool:
    """
    Отправка клика для аналитики (fire-and-forget).
    """
    try:
        async with aiohttp.ClientSession() as session:
            data = {"entity_type": entity_type, "entity_id": entity_id}
            async with session.post(
                f"{API_URL}api/summer/click/", json=data
            ) as response:
                if response.status == 200:
                    logger.info(f"Клик '{entity_type}' (id={entity_id}) зафиксирован.")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Ошибка при трекинге клика: status={response.status}, text={error_text}"
                    )
                    return False
    except Exception as e:
        logger.error(f"Не удалось выполнить запрос к API (summer/click): {e}")
        return False

