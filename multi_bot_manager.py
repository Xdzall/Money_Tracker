import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any
import logging

from telegram.ext import Application
import config
from bot import create_user_bot_app

logger = logging.getLogger("MultiBotManager")

class MultiBotManager:
    """
    Manager for handling multiple Telegram bot instances concurrently for each user in the system.
    """
    def __init__(self):
        self._running_bots: Dict[str, Application] = {}
        self._bot_tasks: Dict[str, asyncio.Task] = {}

    def _get_user_config_path(self, user_id: str) -> Path:
        safe_uid = config.sanitize_user_id(user_id)
        user_dir = config.USERS_DATA_DIR / safe_uid
        os.makedirs(user_dir, exist_ok=True)
        return user_dir / "bot_config.json"

    def get_user_bot_config(self, user_id: str) -> Dict[str, Any]:
        """Get bot configuration for a user."""
        cfg_path = self._get_user_config_path(user_id)
        is_running = user_id in self._running_bots

        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["is_running"] = is_running
                    return data
            except Exception as e:
                logger.error(f"Error reading bot config for {user_id}: {e}")

        # Check if this user is the primary admin from .env
        primary_user = config.TELEGRAM_PRIMARY_USER_ID or "mghazalinurrahman939@gmail.com"
        if user_id.lower() == primary_user.lower() and config.TELEGRAM_BOT_TOKEN:
            return {
                "bot_token": config.TELEGRAM_BOT_TOKEN,
                "bot_token_masked": f"{config.TELEGRAM_BOT_TOKEN[:8]}...{config.TELEGRAM_BOT_TOKEN[-5:]}",
                "telegram_user_id": config.ALLOWED_TELEGRAM_USERS[0] if config.ALLOWED_TELEGRAM_USERS else None,
                "is_active": True,
                "is_running": is_running or ("_primary_" in self._running_bots or user_id in self._running_bots),
                "is_primary_env": True
            }

        return {
            "bot_token": "",
            "bot_token_masked": "",
            "telegram_user_id": None,
            "is_active": False,
            "is_running": False,
            "is_primary_env": False
        }

    def save_user_bot_config(
        self,
        user_id: str,
        bot_token: str,
        telegram_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Save new bot token and Telegram ID for a user."""
        token_clean = bot_token.strip()
        cfg_path = self._get_user_config_path(user_id)
        
        data = {
            "user_id": user_id,
            "bot_token": token_clean,
            "bot_token_masked": f"{token_clean[:8]}...{token_clean[-5:]}" if len(token_clean) > 15 else token_clean,
            "telegram_user_id": int(telegram_user_id) if telegram_user_id else None,
            "is_active": True,
            "updated_at": asyncio.get_event_loop().time()
        }

        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return data

    def delete_user_bot_config(self, user_id: str) -> bool:
        """Delete bot config and deactivate user's bot."""
        cfg_path = self._get_user_config_path(user_id)
        if cfg_path.exists():
            try:
                cfg_path.unlink()
                return True
            except Exception:
                pass
        return False

    async def start_user_bot(self, user_id: str, bot_token: str, telegram_user_id: Optional[int] = None) -> bool:
        """Start or restart a specific user's bot instance."""
        await self.stop_user_bot(user_id)

        allowed_ids = [telegram_user_id] if telegram_user_id else []
        try:
            bot_app = create_user_bot_app(
                user_id=user_id,
                token=bot_token,
                allowed_telegram_ids=allowed_ids
            )
            if not bot_app:
                return False

            await bot_app.initialize()
            await bot_app.start()
            await bot_app.updater.start_polling()

            self._running_bots[user_id] = bot_app
            logger.info(f"✅ Bot untuk user [{user_id}] aktif dan berjalan!")
            return True
        except Exception as e:
            logger.error(f"❌ Gagal menyalakan bot untuk user [{user_id}]: {e}")
            return False

    async def stop_user_bot(self, user_id: str):
        """Stop a specific user's bot instance cleanly."""
        if user_id in self._running_bots:
            bot_app = self._running_bots.pop(user_id, None)
            if bot_app:
                try:
                    logger.info(f"🛑 Menghentikan bot untuk user [{user_id}]...")
                    await bot_app.updater.stop()
                    await bot_app.stop()
                    await bot_app.shutdown()
                except Exception as e:
                    logger.warning(f"Error saat menghentikan bot [{user_id}]: {e}")

    async def start_all_bots(self):
        """Scan and start all registered user bots on system startup."""
        logger.info("🤖 [MultiBotManager] Memeriksa dan menjalankan semua bot terdaftar...")

        # 1. Primary admin bot from .env
        primary_token = config.TELEGRAM_BOT_TOKEN
        primary_user = config.TELEGRAM_PRIMARY_USER_ID or "mghazalinurrahman939@gmail.com"
        if primary_token:
            try:
                await self.start_user_bot(
                    user_id=primary_user,
                    bot_token=primary_token,
                    telegram_user_id=config.ALLOWED_TELEGRAM_USERS[0] if config.ALLOWED_TELEGRAM_USERS else None
                )
            except Exception as e:
                logger.error(f"⚠️ [MultiBotManager] Error saat memulai bot utama: {e}")

        # 2. Check all user directories for bot_config.json
        if config.USERS_DATA_DIR.exists():
            for user_folder in config.USERS_DATA_DIR.iterdir():
                if user_folder.is_dir():
                    cfg_file = user_folder / "bot_config.json"
                    if cfg_file.exists():
                        try:
                            with open(cfg_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            u_id = data.get("user_id") or user_folder.name
                            b_token = data.get("bot_token")
                            tg_id = data.get("telegram_user_id")

                            if b_token and u_id != primary_user:
                                await self.start_user_bot(
                                    user_id=u_id,
                                    bot_token=b_token,
                                    telegram_user_id=tg_id
                                )
                        except Exception as e:
                            logger.error(f"⚠️ [MultiBotManager] Error loading bot for {user_folder.name}: {e}")

    async def stop_all_bots(self):
        """Stop all running bots during server shutdown."""
        logger.info("🛑 [MultiBotManager] Menghentikan semua bot...")
        user_ids = list(self._running_bots.keys())
        for u_id in user_ids:
            await self.stop_user_bot(u_id)

# Global Singleton Manager
bot_manager = MultiBotManager()
