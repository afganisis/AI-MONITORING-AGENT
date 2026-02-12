"""
Message parser with fuzzy matching against Supabase database.

Handles two message formats:
1. Bot format: "Ormon Kurmanbekov #101 OWNERLER EXPRESS INC - Logbook 3 - Aisanem"
2. Manual format: Company on line 1, drivers on lines 2+
"""

import difflib
import re
import time
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, field
from loguru import logger

from app.supabase.client import get_supabase_client, Company, Driver


@dataclass
class MatchedDriver:
    """Successfully matched driver."""
    driver_id: str
    driver_name: str
    original_text: str
    confidence: float


@dataclass
class MatchedCompany:
    """Successfully matched company."""
    company_id: str
    company_name: str
    original_text: str
    confidence: float


@dataclass
class ParseResult:
    """Result of parsing a Telegram message."""
    company: Optional[MatchedCompany]
    drivers: List[MatchedDriver]
    not_found_lines: List[str]
    employee_name: str = ""
    truck_unit: str = ""
    logbook_type: str = ""


class MessageParser:
    """
    Parses Telegram messages and fuzzy-matches against Supabase data.

    Supports two formats:
    1. Bot format (single line):
       "DriverName #TruckUnit CompanyName - Logbook N - EmployeeName"
    2. Manual format (multi-line):
       Line 1: Company name
       Line 2+: One driver name per line
    """

    CACHE_TTL = 300  # 5 minutes

    # Regex for bot format: "Name #unit Company - Logbook N - Employee"
    BOT_FORMAT_RE = re.compile(
        r'^(.+?)\s+#(\d+)\s+(.+?)\s*-\s*Logbook\s+(\d+)\s*-\s*(.+)$',
        re.IGNORECASE
    )

    def __init__(self):
        self._companies: List[Company] = []
        self._last_refresh: float = 0
        self._company_names: Dict[str, Company] = {}
        self._driver_names_by_company: Dict[str, Dict[str, Driver]] = {}
        self._all_driver_names: Dict[str, Tuple[Driver, Company]] = {}

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison: lowercase, strip, collapse spaces."""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    async def refresh_data(self) -> None:
        """Load companies and drivers from Supabase, build lookup index."""
        now = time.time()
        if self._companies and (now - self._last_refresh) < self.CACHE_TTL:
            return

        try:
            supabase = get_supabase_client()
            self._companies = await supabase.get_companies_with_drivers()
            self._last_refresh = now

            self._company_names.clear()
            self._driver_names_by_company.clear()
            self._all_driver_names.clear()

            for company in self._companies:
                norm_name = self._normalize(company.company_name)
                self._company_names[norm_name] = company

                self._driver_names_by_company[company.company_id] = {}
                for driver in company.drivers:
                    norm_driver = self._normalize(driver.driver_name)
                    self._driver_names_by_company[company.company_id][norm_driver] = driver
                    self._all_driver_names[norm_driver] = (driver, company)

            total_drivers = sum(len(c.drivers) for c in self._companies)
            logger.info(
                f"[TG Parser] Loaded {len(self._companies)} companies, "
                f"{total_drivers} drivers from Supabase"
            )

        except Exception as e:
            logger.exception(f"[TG Parser] Failed to refresh data from Supabase: {e}")

    def _try_parse_bot_format(self, text: str) -> Optional[ParseResult]:
        """
        Try to parse bot format: "DriverName #unit CompanyName - Logbook N - Employee"

        Returns ParseResult if format matches, None otherwise.
        """
        match = self.BOT_FORMAT_RE.match(text.strip())
        if not match:
            return None

        driver_name_raw = match.group(1).strip()
        truck_unit = match.group(2).strip()
        company_name_raw = match.group(3).strip()
        logbook_num = match.group(4).strip()
        employee_name = match.group(5).strip()

        logger.info(
            f"[TG Parser] Bot format detected: driver='{driver_name_raw}' "
            f"unit=#{truck_unit} company='{company_name_raw}' "
            f"logbook={logbook_num} employee='{employee_name}'"
        )

        # Match company
        matched_company = self.match_company(company_name_raw)
        if matched_company:
            logger.info(
                f"[TG Parser] Company matched: '{company_name_raw}' -> "
                f"'{matched_company.company_name}' (conf={matched_company.confidence:.2f})"
            )

        # Match driver
        company_id = matched_company.company_id if matched_company else None
        driver_result = self.match_driver(driver_name_raw, company_id)

        matched_drivers = []
        not_found = []

        if driver_result:
            driver_match, auto_company = driver_result
            matched_drivers.append(driver_match)
            if not matched_company and auto_company:
                matched_company = auto_company
            logger.info(
                f"[TG Parser] Driver matched: '{driver_name_raw}' -> "
                f"'{driver_match.driver_name}' (conf={driver_match.confidence:.2f})"
            )
        else:
            not_found.append(driver_name_raw)
            logger.warning(f"[TG Parser] Driver not found in DB: '{driver_name_raw}'")

        return ParseResult(
            company=matched_company,
            drivers=matched_drivers,
            not_found_lines=not_found,
            employee_name=employee_name,
            truck_unit=truck_unit,
            logbook_type=f"Logbook {logbook_num}",
        )

    def match_company(self, text: str) -> Optional[MatchedCompany]:
        """Fuzzy match company name against known companies."""
        norm_text = self._normalize(text)
        if not norm_text:
            return None

        # Exact match
        if norm_text in self._company_names:
            company = self._company_names[norm_text]
            return MatchedCompany(
                company_id=company.company_id,
                company_name=company.company_name,
                original_text=text,
                confidence=1.0
            )

        # Fuzzy match
        all_names = list(self._company_names.keys())
        matches = difflib.get_close_matches(norm_text, all_names, n=1, cutoff=0.5)
        if matches:
            company = self._company_names[matches[0]]
            confidence = difflib.SequenceMatcher(None, norm_text, matches[0]).ratio()
            return MatchedCompany(
                company_id=company.company_id,
                company_name=company.company_name,
                original_text=text,
                confidence=confidence
            )

        # Substring match
        for norm_name, company in self._company_names.items():
            if norm_text in norm_name or norm_name in norm_text:
                return MatchedCompany(
                    company_id=company.company_id,
                    company_name=company.company_name,
                    original_text=text,
                    confidence=0.7
                )

        return None

    def match_driver(
        self,
        text: str,
        company_id: Optional[str] = None
    ) -> Optional[Tuple[MatchedDriver, Optional[MatchedCompany]]]:
        """Fuzzy match driver name against known drivers."""
        norm_text = self._normalize(text)
        if not norm_text or len(norm_text) < 3:
            return None

        # Search within specific company first
        if company_id and company_id in self._driver_names_by_company:
            drivers_map = self._driver_names_by_company[company_id]

            if norm_text in drivers_map:
                driver = drivers_map[norm_text]
                return (
                    MatchedDriver(
                        driver_id=driver.driver_id,
                        driver_name=driver.driver_name,
                        original_text=text,
                        confidence=1.0
                    ),
                    None
                )

            all_names = list(drivers_map.keys())
            matches = difflib.get_close_matches(norm_text, all_names, n=1, cutoff=0.5)
            if matches:
                driver = drivers_map[matches[0]]
                confidence = difflib.SequenceMatcher(None, norm_text, matches[0]).ratio()
                return (
                    MatchedDriver(
                        driver_id=driver.driver_id,
                        driver_name=driver.driver_name,
                        original_text=text,
                        confidence=confidence
                    ),
                    None
                )

        # Search across all companies
        if norm_text in self._all_driver_names:
            driver, company = self._all_driver_names[norm_text]
            return (
                MatchedDriver(
                    driver_id=driver.driver_id,
                    driver_name=driver.driver_name,
                    original_text=text,
                    confidence=1.0
                ),
                MatchedCompany(
                    company_id=company.company_id,
                    company_name=company.company_name,
                    original_text=company.company_name,
                    confidence=1.0
                )
            )

        all_names = list(self._all_driver_names.keys())
        matches = difflib.get_close_matches(norm_text, all_names, n=1, cutoff=0.5)
        if matches:
            driver, company = self._all_driver_names[matches[0]]
            confidence = difflib.SequenceMatcher(None, norm_text, matches[0]).ratio()
            return (
                MatchedDriver(
                    driver_id=driver.driver_id,
                    driver_name=driver.driver_name,
                    original_text=text,
                    confidence=confidence
                ),
                MatchedCompany(
                    company_id=company.company_id,
                    company_name=company.company_name,
                    original_text=company.company_name,
                    confidence=confidence
                )
            )

        return None

    async def parse_message(self, text: str) -> ParseResult:
        """
        Parse a Telegram message into company + drivers.

        Tries bot format first, then falls back to manual multi-line format.
        """
        await self.refresh_data()

        # Try bot format: "DriverName #unit CompanyName - Logbook N - Employee"
        bot_result = self._try_parse_bot_format(text)
        if bot_result:
            return bot_result

        # Fallback: manual multi-line format
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        if not lines:
            return ParseResult(company=None, drivers=[], not_found_lines=[])

        matched_company: Optional[MatchedCompany] = None
        matched_drivers: List[MatchedDriver] = []
        not_found: List[str] = []

        # Line 1: try as company name
        first_line = lines[0]
        matched_company = self.match_company(first_line)

        if matched_company:
            logger.info(
                f"[TG Parser] Company matched: '{first_line}' -> "
                f"'{matched_company.company_name}' (conf={matched_company.confidence:.2f})"
            )
            driver_lines = lines[1:]
        else:
            driver_lines = lines

        for line in driver_lines:
            company_id = matched_company.company_id if matched_company else None
            result = self.match_driver(line, company_id)

            if result:
                driver_match, auto_company = result
                matched_drivers.append(driver_match)
                if not matched_company and auto_company:
                    matched_company = auto_company
                    logger.info(
                        f"[TG Parser] Auto-detected company from driver: "
                        f"'{auto_company.company_name}'"
                    )
                logger.info(
                    f"[TG Parser] Driver matched: '{line}' -> "
                    f"'{driver_match.driver_name}' (conf={driver_match.confidence:.2f})"
                )
            else:
                not_found.append(line)
                logger.warning(f"[TG Parser] Not found in DB: '{line}'")

        return ParseResult(
            company=matched_company,
            drivers=matched_drivers,
            not_found_lines=not_found
        )


# Global instance
message_parser = MessageParser()
