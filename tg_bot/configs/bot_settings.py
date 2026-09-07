import os

from dotenv import load_dotenv


load_dotenv()

DEBUG = os.getenv('BOT_DEBUG') == 'True'

if DEBUG:
    BOT_TOKEN = os.environ.get("TEST_BOT_TOKEN")
else:
    BOT_TOKEN = os.environ.get("BOT_TOKEN")

if DEBUG:
    API_URL = os.getenv("LOCAL_KIBER_API_URL")
else:
    API_URL = os.getenv("KIBER_API_URL")

# Раздел «Лето с KLiK» скрыт из меню бота.
# Код сценария сохранён целиком: чтобы вернуть кнопку и её обработчики,
# достаточно поставить True.
SUMMER_FEATURE_ENABLED = False
