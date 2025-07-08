import os
from dotenv import load_dotenv

load_dotenv()

# Общие настройки
TOKEN = os.getenv("TG_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

# Настройки для парсера объявлений
LOGIN_URL = os.getenv("LOGIN_URL", "https://on.econ.msu.ru/login/index.php")
COURSES_URL = os.getenv("COURSES_URL", "https://on.econ.msu.ru/my/courses.php")
USER_DATA_FILE = os.getenv("USER_DATA_FILE", "user_data.json")
ANNOUNCEMENTS_FILE = os.getenv("ANNOUNCEMENTS_FILE", "announcements.json")

SCHEDULE_FILE = "timetable.csv"