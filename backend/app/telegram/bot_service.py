"""
Telegram Bot Service for AI Monitoring.

Reads driver/company names from input group, runs Smart Analyze,
sends results to output group. All results saved to JSON log.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger
from telegram import Bot, Update, ReactionTypeEmoji
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from app.config import get_settings
from app.telegram.parser import message_parser
from app.telegram.formatter import format_scan_results, format_not_found_warning
from app.fortex.client import FortexAPIClient

# Directory for saving all scan results
SCAN_LOG_DIR = Path("scan_logs")
SCAN_LOG_DIR.mkdir(exist_ok=True)


class TelegramBotService:
    """Main Telegram bot service."""

    def __init__(self):
        self._app: Optional[Application] = None
        self._task: Optional[asyncio.Task] = None
        self._bot: Optional[Bot] = None
        self._running = False
        self._started_at: float = 0

    async def start(self) -> None:
        """Start Telegram bot polling in background."""
        settings = get_settings()

        if not settings.tg_bot:
            logger.warning("[TG Bot] No TG_BOT token — disabled")
            return

        try:
            self._app = Application.builder().token(settings.tg_bot).build()
            self._bot = self._app.bot

            self._app.add_handler(
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & filters.Chat(settings.tg_group_input),
                    self._handle_message,
                )
            )

            await self._app.initialize()
            await self._app.start()

            self._started_at = time.time()
            self._running = True
            self._task = asyncio.create_task(self._poll_loop())

            bot_info = await self._bot.get_me()
            logger.info(f"[TG Bot] Started @{bot_info.username} | in={settings.tg_group_input} out={settings.tg_group_output}")

        except Exception as e:
            logger.exception(f"[TG Bot] Failed to start: {e}")
            self._running = False

    async def _poll_loop(self) -> None:
        """Run polling with auto-restart on failure."""
        while self._running:
            try:
                updater = self._app.updater
                await updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=["message"],
                )
                while self._running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[TG Bot] Polling error, restarting in 5s: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop Telegram bot gracefully."""
        self._running = False
        try:
            if self._app and self._app.updater and self._app.updater.running:
                await self._app.updater.stop()
            if self._app and self._app.running:
                await self._app.stop()
                await self._app.shutdown()
        except Exception as e:
            logger.error(f"[TG Bot] Shutdown error: {e}")

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[TG Bot] Stopped")

    async def _send_long_message(self, chat_id: int, text: str) -> None:
        """Send message, splitting if > 4096 chars."""
        MAX_LEN = 4096
        if len(text) <= MAX_LEN:
            await self._bot.send_message(chat_id=chat_id, text=text)
            return

        parts = text.split("\n\n")
        current = ""
        for part in parts:
            candidate = (current + "\n\n" + part) if current else part
            if len(candidate) > MAX_LEN:
                if current:
                    await self._bot.send_message(chat_id=chat_id, text=current.strip())
                current = part
            else:
                current = candidate
        if current.strip():
            await self._bot.send_message(chat_id=chat_id, text=current.strip())

    async def _set_reaction(self, chat_id: int, message_id: int, emoji: str) -> None:
        """Set reaction on a message (silent fail)."""
        try:
            await self._bot.set_message_reaction(
                chat_id=chat_id,
                message_id=message_id,
                reaction=[ReactionTypeEmoji(emoji=emoji)],
            )
        except Exception as e:
            logger.debug(f"[TG Bot] Reaction {emoji} failed: {e}")

    def _save_scan_log(
        self,
        message_text: str,
        company_name: str,
        driver_results: list,
        parse_info: dict,
        duration: float,
    ) -> None:
        """Save full scan results to JSON log file."""
        try:
            now = datetime.now()
            entry = {
                "timestamp": now.isoformat(),
                "message": message_text,
                "company": company_name,
                "parse": parse_info,
                "duration_sec": round(duration, 2),
                "drivers": [],
            }
            for dr in driver_results:
                entry["drivers"].append({
                    "driver_id": dr.get("driver_id", ""),
                    "driver_name": dr.get("driver_name", ""),
                    "error_count": len(dr.get("errors", [])),
                    "errors": dr.get("errors", []),
                    "scan_error": dr.get("scan_error"),
                })

            # One file per day
            log_file = SCAN_LOG_DIR / f"{now.strftime('%Y-%m-%d')}.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

            logger.debug(f"[TG Bot] Scan log saved to {log_file}")
        except Exception as e:
            logger.warning(f"[TG Bot] Failed to save scan log: {e}")

    async def _handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle incoming message from input group."""
        message = update.effective_message
        if not message or not message.text:
            return

        # Skip old messages (before bot start)
        if message.date and message.date.timestamp() < self._started_at:
            return

        chat_id = message.chat_id
        message_id = message.message_id
        text = message.text.strip()
        settings = get_settings()

        if len(text) < 3:
            return

        logger.info(f"[TG Bot] << {text[:80]}")
        start_time = time.time()

        # React: processing
        await self._set_reaction(chat_id, message_id, "\U0001f440")

        try:
            # Parse
            parse_result = await message_parser.parse_message(text)

            if not parse_result.company or not parse_result.drivers:
                logger.warning(f"[TG Bot] No match: {text[:60]}")
                await self._set_reaction(chat_id, message_id, "\U0001f44e")
                return

            company = parse_result.company
            drivers = parse_result.drivers
            logger.info(f"[TG Bot] {company.company_name} -> {[d.driver_name for d in drivers]}")

            # Run Smart Analyze + Monitoring Overview in parallel
            driver_results, company_total = await asyncio.gather(
                self._run_smart_analyze_with_retry(
                    company_id=company.company_id,
                    driver_ids=[d.driver_id for d in drivers],
                    driver_names={d.driver_id: d.driver_name for d in drivers},
                ),
                self._get_company_error_count(company.company_id),
            )

            scan_duration = time.time() - start_time

            # Save ALL results to log (including hidden errors)
            self._save_scan_log(
                message_text=text,
                company_name=company.company_name,
                driver_results=driver_results,
                parse_info={
                    "company": company.company_name,
                    "company_id": company.company_id,
                    "confidence": company.confidence,
                    "drivers": [{"name": d.driver_name, "id": d.driver_id} for d in drivers],
                    "employee": parse_result.employee_name,
                    "truck_unit": parse_result.truck_unit,
                    "logbook": parse_result.logbook_type,
                },
                duration=scan_duration,
            )

            # Format (hidden errors excluded from display but counted)
            result_text = format_scan_results(
                company_name=company.company_name,
                driver_results=driver_results,
                scan_duration_sec=scan_duration,
                employee_name=parse_result.employee_name,
                truck_unit=parse_result.truck_unit,
                logbook_type=parse_result.logbook_type,
                company_total_errors=company_total,
            )

            if parse_result.not_found_lines:
                result_text += "\n\n" + format_not_found_warning(parse_result.not_found_lines)

            # Send
            await self._send_long_message(settings.tg_group_output, result_text)

            # React: done
            await self._set_reaction(chat_id, message_id, "\U0001f44d")
            logger.info(f"[TG Bot] Done: {company.company_name} | {scan_duration:.1f}s")

        except Exception as e:
            logger.exception(f"[TG Bot] Error: {e}")
            await self._set_reaction(chat_id, message_id, "\U0001f44e")
            try:
                await self._bot.send_message(
                    chat_id=settings.tg_group_output,
                    text=f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430: {str(e)[:300]}",
                )
            except Exception:
                pass

    async def _get_company_error_count(self, company_id: str) -> Optional[int]:
        """Get total error count for company from monitoring overview."""
        settings = get_settings()
        fortex = FortexAPIClient(
            base_url=settings.fortex_api_url,
            auth_token=settings.fortex_auth_token,
            system_name=settings.fortex_system_name,
        )
        try:
            overview = await fortex.get_monitoring_overview()
            for c in overview.companies:
                if c.id == company_id:
                    return c.total
            return None
        except Exception as e:
            logger.debug(f"[TG Bot] Overview failed: {e}")
            return None
        finally:
            await fortex.close()

    async def _run_smart_analyze_with_retry(
        self,
        company_id: str,
        driver_ids: list,
        driver_names: dict,
        retries: int = 2,
    ) -> list:
        """Run Smart Analyze with retry on failure."""
        settings = get_settings()
        last_error = None

        for attempt in range(1, retries + 1):
            fortex = FortexAPIClient(
                base_url=settings.fortex_api_url,
                auth_token=settings.fortex_auth_token,
                system_name=settings.fortex_system_name,
            )
            try:
                smart_data = await fortex.get_smart_analyze(company_id)

                driver_errors_map = {}
                for driver_log in smart_data.drivers:
                    did = driver_log.driver_id or driver_log.driverId
                    if did in driver_ids:
                        errors_list = []
                        for err in driver_log.logCheckErrors:
                            errors_list.append({
                                "errorMessage": err.errorMessage or err.message or "Unknown",
                                "errorTime": err.errorTime or err.timestamp,
                                "errorType": err.errorType or err.type,
                                "eventCode": err.eventCode,
                            })
                        driver_errors_map[did] = errors_list

                results = []
                for did in driver_ids:
                    results.append({
                        "driver_id": did,
                        "driver_name": driver_names.get(did, did[:8]),
                        "errors": driver_errors_map.get(did, []),
                    })

                total = sum(len(r["errors"]) for r in results)
                logger.info(f"[TG Bot] Smart Analyze: {total} errors (attempt {attempt})")
                return results

            except Exception as e:
                last_error = e
                logger.warning(f"[TG Bot] Smart Analyze attempt {attempt} failed: {e}")
                if attempt < retries:
                    await asyncio.sleep(2)
            finally:
                await fortex.close()

        # All retries failed
        return [{
            "driver_id": did,
            "driver_name": driver_names.get(did, did[:8]),
            "errors": [],
            "scan_error": str(last_error),
        } for did in driver_ids]


# Global singleton
telegram_bot = TelegramBotService()
