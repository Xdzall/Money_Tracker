import os
import sys
import time
import threading
import asyncio
import uvicorn

import config
from bot import create_bot_app
from excel_manager import ExcelManager

def run_web_server():
    print(f"\n🚀 [Web Dashboard] Berjalan di http://localhost:{config.WEB_PORT} (atau http://{config.WEB_HOST}:{config.WEB_PORT})")
    uvicorn_config = uvicorn.Config(
        app="app:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(uvicorn_config)
    server.run()

def run_telegram_bot_loop():
    while True:
        config.reload_config()
        token = config.TELEGRAM_BOT_TOKEN
        if token:
            print(f"🤖 [Telegram Bot] Menghubungkan bot dengan token ({token[:8]}...)...")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                bot_app = create_bot_app()
                if bot_app:
                    print("✅ [Telegram Bot] Bot aktif dan siap menerima pesan!")
                    bot_app.run_polling(close_loop=False)
            except Exception as e:
                print(f"⚠️  [Telegram Bot] Error koneksi bot: {e}")
                time.sleep(5)
        else:
            time.sleep(3)

def main():
    print("=" * 60)
    print("      💰 MONEY TRACKING APP (WEB + TELEGRAM + EXCEL)       ")
    print("=" * 60)
    
    em = ExcelManager()
    print("✅ [Excel] File MoneyTracking.xlsx siap dan bersih dari 0.")

    # Start Telegram bot polling thread
    bot_thread = threading.Thread(target=run_telegram_bot_loop, daemon=True)
    bot_thread.start()

    # Run Web Server on main thread
    run_web_server()

if __name__ == "__main__":
    main()
