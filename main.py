import os
import sys
import uvicorn
import config
from excel_manager import ExcelManager

def main():
    print("=" * 60)
    print("      💰 MONEY TRACKING APP (WEB + TELEGRAM + EXCEL)       ")
    print("=" * 60)
    
    # Initialize Excel database if not created
    em = ExcelManager()
    print("✅ [Excel] File MoneyTracking.xlsx siap.")

    # Run Web Server (Telegram Bot starts automatically via FastAPI Lifespan)
    print(f"🚀 [Web Server] Berjalan di port {config.WEB_PORT}...")
    uvicorn.run(
        "app:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
