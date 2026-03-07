"""
CD-23 live scraper using requests + BeautifulSoup with Selenium fallback.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urljoin

import requests  # type: ignore[import-untyped]

try:
    from bs4 import BeautifulSoup as BS4BeautifulSoup

    BS4_AVAILABLE = True
except Exception:  # pragma: no cover - defensive import
    BS4BeautifulSoup = None  # type: ignore[assignment]
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)

WEBDRIVER: Any = None
CHROME_OPTIONS: Any = None
try:
    from selenium import webdriver as selenium_webdriver
    from selenium.webdriver.chrome.options import Options as chrome_options_class

    WEBDRIVER = selenium_webdriver
    CHROME_OPTIONS = chrome_options_class
    SELENIUM_AVAILABLE = True
except Exception:  # pragma: no cover - defensive import
    SELENIUM_AVAILABLE = False


@dataclass(frozen=True)
class AuctionTarget:
    name: str
    base_url: str
    listing_paths: tuple[str, ...]


class AuctionSiteScraper:
    """
    Best-effort scraper for public listing pages.

    The parser is intentionally selector-flexible so it can keep extracting
    partial data if source markup changes.
    """

    TARGETS: tuple[AuctionTarget, ...] = (
        AuctionTarget(
            name="RAMADBK",
            base_url="https://www.ramadbk.com",
            listing_paths=("/stock_list.php", "/search_by_usual.php"),
        ),
    )

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
    }

    _PASSENGER_BODY_HINTS = {
        "sedan",
        "suv",
        "hatchback",
        "wagon",
        "coupe",
        "convertible",
        "van",
        "minivan",
    }
    _NON_PASSENGER_HINTS = {
        "truck",
        "bus",
        "forklift",
        "excavator",
        "tractor",
        "machinery",
        "crane",
        "dump",
        "trailer",
        "carrier",
        "loader",
        "bike",
        "motorcycle",
    }

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds
        self._http = requests.Session()
        self._http.headers.update(self._HEADERS)

    def scrape(self, count: int = 10) -> list[dict[str, Any]]:
        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup is not installed. Live scraper disabled for this run.")
            return []

        rows: list[dict[str, Any]] = []
        seen_stock: set[str] = set()

        for target in self.TARGETS:
            for path in target.listing_paths:
                if len(rows) >= count:
                    return rows[:count]

                page_url = urljoin(target.base_url, path)
                scraped = self._scrape_page(target, page_url, count - len(rows))
                for row in scraped:
                    stock_no = str(row.get("stock_no") or "")
                    if stock_no and stock_no in seen_stock:
                        continue
                    if stock_no:
                        seen_stock.add(stock_no)
                    rows.append(row)
                    if len(rows) >= count:
                        return rows[:count]

                # RAMADBK exposes additional stock pages via `?page=N`.
                if "search_by_usual.php" in page_url:
                    empty_pages = 0
                    for page in range(1, 200):
                        if len(rows) >= count:
                            return rows[:count]

                        sep = "&" if "?" in page_url else "?"
                        paged_url = f"{page_url}{sep}page={page}"
                        paged_rows = self._scrape_page(target, paged_url, count - len(rows))
                        added = 0
                        for row in paged_rows:
                            stock_no = str(row.get("stock_no") or "")
                            if stock_no and stock_no in seen_stock:
                                continue
                            if stock_no:
                                seen_stock.add(stock_no)
                            rows.append(row)
                            added += 1
                            if len(rows) >= count:
                                return rows[:count]

                        if added == 0:
                            empty_pages += 1
                            if empty_pages >= 3:
                                break
                        else:
                            empty_pages = 0

        return rows[:count]

    def _scrape_page(
        self, target: AuctionTarget, page_url: str, limit: int
    ) -> list[dict[str, Any]]:
        try:
            response = self._http.get(page_url, timeout=self.timeout_seconds)
            response.raise_for_status()
            html = response.text
        except Exception as exc:
            logger.warning("Requests scrape failed for %s (%s): %s", target.name, page_url, exc)
            html = self._fetch_with_selenium(page_url)
            if not html:
                return []

        soup = BS4BeautifulSoup(html, "lxml")
        cards = self._extract_cards(soup)
        rows: list[dict[str, Any]] = []

        for card in cards[:limit]:
            row = self._parse_card(card, target, page_url)
            if row:
                rows.append(row)

        logger.info("Scraped %s rows from %s", len(rows), page_url)
        return rows

    def _fetch_with_selenium(self, page_url: str) -> str:
        if not SELENIUM_AVAILABLE or WEBDRIVER is None or CHROME_OPTIONS is None:
            return ""

        driver = None
        try:
            options = CHROME_OPTIONS()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument(f"user-agent={self._HEADERS['User-Agent']}")
            driver = WEBDRIVER.Chrome(options=options)
            driver.get(page_url)
            return str(driver.page_source)
        except Exception as exc:
            logger.warning("Selenium scrape failed for %s: %s", page_url, exc)
            return ""
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass

    def _extract_cards(self, soup: Any) -> list[Any]:
        selectors = (
            "section[id^='VEHID']",
            ".stock_list_first",
            ".car-list-item",
            ".vehicle-item",
            ".listing-item",
            ".car-item",
            ".product-item",
            "article",
        )

        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cast(list[Any], cards)
        return []

    def _parse_card(self, card: Any, target: AuctionTarget, page_url: str) -> dict[str, Any] | None:
        title = self._text(card, "h2 a, .title, .car-title, h2, h3")
        if not title:
            return None

        make, model = self._extract_make_model(title)
        year = self._extract_year(title) or datetime.now(UTC).year

        detail_url = self._link(card, page_url, "a[href]")
        if not self._is_passenger_vehicle(title=title, detail_url=detail_url):
            return None
        image_urls = self._images(card, page_url)
        card_text = card.get_text(" ", strip=True)
        price = self._extract_price(
            self._text(card, "strong[id^='span_dummy_price'], .price, .car-price, [class*='price']")
        )
        if price is None:
            price = self._extract_price_from_text(card_text)
        mileage = self._extract_labeled_number(card_text, "Mileage", "KM")
        engine_cc = self._extract_labeled_number(card_text, "Engine", "CC")
        fuel_type = self._extract_labeled_value(card_text, "Fuel")
        transmission = self._extract_labeled_value(card_text, "Transmission")

        stock_no = (
            self._extract_stock_no_from_text(card_text)
            or self._extract_stock_no(detail_url)
            or f"{target.name}-{abs(hash(title)) % 1000000}"
        )
        now = datetime.now(UTC).isoformat()

        row: dict[str, Any] = {
            "stock_no": stock_no,
            "chassis": None,
            "make": make,
            "model": model or "Unknown",
            "year": year,
            "price_jpy": price or 0,
            "mileage_km": mileage,
            "engine_cc": engine_cc,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "status": "AVAILABLE",
            "vehicle_url": detail_url,
            "image_url": image_urls[0] if image_urls else None,
            "images": image_urls,
            "scraped_at": now,
            "source": f"{target.name}_BS4_SELENIUM",
        }
        if detail_url:
            detail_data = self._scrape_detail_data(detail_url)
            if detail_data:
                row.update({k: v for k, v in detail_data.items() if v is not None})
                detail_images = detail_data.get("images") or []
                if isinstance(detail_images, list) and detail_images:
                    row["images"] = detail_images
                    row["image_url"] = detail_images[0]
        return row

    def _scrape_detail_data(self, detail_url: str) -> dict[str, Any]:
        if not BS4_AVAILABLE:
            return {}
        try:
            response = self._http.get(detail_url, timeout=self.timeout_seconds)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to scrape RAMADBK detail page %s: %s", detail_url, exc)
            return {}

        soup = BS4BeautifulSoup(response.text, "lxml")
        data: dict[str, Any] = {}

        # Parse key/value rows in "Vehicle Details".
        for row in soup.select("div.row"):
            label_node = row.select_one(
                "div.col-lg-5 strong, div.col-md-5 strong, div.col-sm-5 strong, div.col-xs-5 strong"
            )
            value_node = row.select_one("div.col-lg-7, div.col-md-7, div.col-sm-7, div.col-xs-7")
            if not label_node or not value_node:
                continue
            label = label_node.get_text(" ", strip=True).lower().rstrip(".")
            value = value_node.get_text(" ", strip=True)
            if not value:
                continue
            if label == "stock no":
                data["stock_no"] = value
            elif label == "make":
                data["make"] = value.title()
            elif label == "model":
                data["model"] = value
            elif label == "reg. year":
                data["reg_year"] = value
                yr = self._extract_year(value)
                if yr:
                    data["year"] = yr
            elif label == "type":
                data["vehicle_type"] = value
                data["body_type"] = value
            elif label == "grade":
                data["grade"] = value
            elif label == "chassis":
                data["chassis"] = value
            elif label == "mileage":
                mileage = self._extract_number(value)
                if mileage is not None:
                    data["mileage_km"] = mileage
            elif label == "engine":
                engine = self._extract_number(value)
                if engine is not None:
                    data["engine_cc"] = engine
            elif label == "transmission":
                data["transmission"] = value
            elif label == "fuel":
                data["fuel_type"] = value
            elif label == "steering":
                data["steering"] = value
            elif label == "drive":
                data["drive"] = value
            elif label == "seats":
                seats = self._extract_number(value)
                if seats is not None:
                    data["seats"] = seats
            elif label == "doors":
                doors = self._extract_number(value)
                if doors is not None:
                    data["doors"] = doors
            elif label == "colour":
                data["color"] = value
            elif label == "location":
                data["location"] = value.replace("ť", "»")

        options_header = soup.find(
            "h3", class_="other_stkhead", string=re.compile(r"Options", re.IGNORECASE)
        )
        if options_header:
            options_ul = options_header.find_next("ul", class_="acc_ulli")
            if options_ul:
                options_items = [li.get_text(" ", strip=True) for li in options_ul.select("li")]
                options_items = [item for item in options_items if item]
                if options_items:
                    data["options"] = " | ".join(options_items)

        remarks_header = soup.find(
            "h3", class_="other_stkhead", string=re.compile(r"Other Remarks", re.IGNORECASE)
        )
        if remarks_header:
            remarks_ul = remarks_header.find_next("ul", class_="acc_ulli")
            if remarks_ul:
                remarks = " | ".join(
                    filter(
                        None,
                        [
                            line.strip()
                            for line in remarks_ul.get_text("\n", strip=True).split("\n")
                        ],
                    )
                )
                if remarks:
                    data["other_remarks"] = remarks

        detail_images: list[str] = []
        seen: set[str] = set()
        for img in soup.select("img[src], img[data-src]"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
            full = urljoin(detail_url, src.strip())
            lower = full.lower()
            if "/vimgs/" not in lower and "/car_images/" not in lower:
                continue
            if "/vimgs/thumb/" in lower:
                full = full.replace("/VIMGS/thumb/", "/VIMGS/images/").replace(
                    "/vimgs/thumb/", "/VIMGS/images/"
                )
                filename = full.rsplit("/", 1)[-1]
                if filename.startswith("T"):
                    full = full.rsplit("/", 1)[0] + "/" + filename[1:]
            elif "/vimgs/medium/" in lower:
                full = full.replace("/VIMGS/medium/", "/VIMGS/images/").replace(
                    "/vimgs/medium/", "/VIMGS/images/"
                )
            key = full.rsplit("/", 1)[-1].lower()
            if key in seen:
                continue
            seen.add(key)
            detail_images.append(full)

        for match in re.findall(
            r"https?://[^\"'\s>]+/VIMGS/[^\"'\s<]+", response.text, flags=re.IGNORECASE
        ):
            full = match
            lower = full.lower()
            if "/vimgs/thumb/" in lower:
                full = full.replace("/VIMGS/thumb/", "/VIMGS/images/").replace(
                    "/vimgs/thumb/", "/VIMGS/images/"
                )
                filename = full.rsplit("/", 1)[-1]
                if filename.startswith("T"):
                    full = full.rsplit("/", 1)[0] + "/" + filename[1:]
            elif "/vimgs/medium/" in lower:
                full = full.replace("/VIMGS/medium/", "/VIMGS/images/").replace(
                    "/vimgs/medium/", "/VIMGS/images/"
                )
            key = full.rsplit("/", 1)[-1].lower()
            if key in seen:
                continue
            seen.add(key)
            detail_images.append(full)

        if detail_images:
            data["images"] = detail_images[:40]

        return data

    def _is_passenger_vehicle(self, title: str, detail_url: str | None) -> bool:
        text = f"{title} {detail_url or ''}".lower()

        # Exclude obvious non-passenger categories first.
        for token in self._NON_PASSENGER_HINTS:
            if token in text:
                return False

        # Allow if explicit passenger body type is visible.
        for token in self._PASSENGER_BODY_HINTS:
            if token in text:
                return True

        # Default to include unknown passenger-looking listings rather than over-dropping.
        return True

    @staticmethod
    def _text(node: Any, selector: str) -> str | None:
        item = node.select_one(selector)
        if not item:
            return None
        text = item.get_text(" ", strip=True)
        return text or None

    @staticmethod
    def _link(node: Any, base_url: str, selector: str) -> str | None:
        item = node.select_one(selector)
        href = item.get("href") if item else None
        if not href:
            return None
        return urljoin(base_url, str(href))

    @staticmethod
    def _images(node: Any, base_url: str) -> list[str]:
        urls: list[str] = []
        for img in node.select("img[src], img[data-src]"):
            src = img.get("src") or img.get("data-src")
            if src:
                urls.append(urljoin(base_url, src))
        return urls[:5]

    @staticmethod
    def _extract_make_model(title: str) -> tuple[str, str]:
        # RAMADBK titles may include appended pricing text like "FOB: ...".
        title = re.split(r"\bFOB\b\s*:", title, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        words = title.split()
        if not words:
            return ("Unknown", "Unknown")
        make = words[0].title()
        model = " ".join(words[1:]).strip() or "Unknown"
        return make, model

    @staticmethod
    def _extract_year(text: str) -> int | None:
        match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _extract_price(text: str | None) -> int | None:
        if not text:
            return None
        value = re.sub(r"[^\d]", "", text)
        return int(value) if value else None

    @staticmethod
    def _extract_price_from_text(text: str | None) -> int | None:
        if not text:
            return None
        match = re.search(r"FOB\s*:\s*([\d,]+)", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def _extract_number(text: str | None) -> int | None:
        if not text:
            return None
        match = re.search(r"(\d[\d,]*)", text)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))

    @staticmethod
    def _extract_stock_no(url: str | None) -> str | None:
        if not url:
            return None
        match = re.search(r"_(\d+)\.html?$", url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _extract_stock_no_from_text(text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(r"Stock\s*No\.?\s*:\s*([A-Za-z0-9-]+)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _extract_labeled_number(text: str | None, label: str, unit: str) -> int | None:
        if not text:
            return None
        pattern = rf"{re.escape(label)}\s*([0-9,]+)\s*{re.escape(unit)}"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))

    @staticmethod
    def _extract_labeled_value(text: str | None, label: str) -> str | None:
        if not text:
            return None
        pattern = (
            rf"{re.escape(label)}\s*([A-Za-z0-9/+ -]+?)"
            rf"(?:\s+(?:Transmission|Engine|Mileage|Options|Stock|Chassis|FOB)\b|$)"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        value = match.group(1).strip()
        return value or None
