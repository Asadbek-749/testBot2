import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(id_str) for id_str in os.getenv("ADMIN_IDS", "").split(",") if id_str.strip().isdigit()]

# Agar DATABASE_URL berilgan bo'lsa psycopg2, bo'lmasa sqlite3 ishlatiladi
DATABASE_URL = os.getenv("DATABASE_URL", None)
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite3")
