import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# Load .env if present
load_dotenv(ENV_FILE, override=True)

# Excel Settings
EXCEL_FILE = os.getenv("EXCEL_FILE", str(BASE_DIR / "MoneyTracking.xlsx"))
BACKUP_DIR = os.getenv("BACKUP_DIR", str(BASE_DIR / "backups"))

# Web Server Settings
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

def get_allowed_users():
    return [
        int(uid.strip())
        for uid in os.getenv("ALLOWED_TELEGRAM_USERS", "").split(",")
        if uid.strip().isdigit()
    ]

ALLOWED_TELEGRAM_USERS = get_allowed_users()

def reload_config():
    global TELEGRAM_BOT_TOKEN, ALLOWED_TELEGRAM_USERS, WEB_HOST, WEB_PORT, EXCEL_FILE
    load_dotenv(ENV_FILE, override=True)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    ALLOWED_TELEGRAM_USERS = get_allowed_users()
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
    EXCEL_FILE = os.getenv("EXCEL_FILE", str(BASE_DIR / "MoneyTracking.xlsx"))

def save_env_settings(bot_token: str, allowed_users: str = ""):
    lines = []
    lines.append(f"WEB_HOST={WEB_HOST}\n")
    lines.append(f"WEB_PORT={WEB_PORT}\n")
    lines.append(f"TELEGRAM_BOT_TOKEN={bot_token.strip()}\n")
    lines.append(f"ALLOWED_TELEGRAM_USERS={allowed_users.strip()}\n")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    reload_config()

# Defaults
DEFAULT_INCOME_CATEGORIES = [
    "Gaji",
    "Bonus / THR",
    "Bisnis / Freelance",
    "Investasi / Dividen",
    "Hadiah / Cashback",
    "Lain-lain"
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Makanan & Minuman",
    "Belanja Bulanan",
    "Tagihan & Utilitas",
    "Transportasi & Bensin",
    "Cicilan & Hutang",
    "Pendidikan / Kursus",
    "Kesehatan & Obat",
    "Hiburan & Rekreasi",
    "Sedekah & Donasi",
    "Keluarga",
    "Lain-lain"
]

DEFAULT_WALLETS = [
    "SeaBank",
    "BCA",
    "Mandiri",
    "BRI",
    "BNI",
    "Bank Jago",
    "Cash / Tunai",
    "GoPay",
    "OVO",
    "ShopeePay",
    "DANA"
]
