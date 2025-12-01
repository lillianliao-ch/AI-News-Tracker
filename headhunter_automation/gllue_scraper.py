import asyncio
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, TimeoutError, async_playwright


@dataclass
class CandidateRecord:
    name: str
    city: Optional[str] = None
    work_experience: Optional[List[str]] = None
    source_url: Optional[str] = None


class GllueScraper:
    """Automation helper for Gllue CRM candidate pages."""

    LOGIN_URL = "https://rpt.gllue.com/crm#dashboard"
    DEFAULT_LIST_URL = "https://rpt.gllue.com/crm#candidate/list?gql=owner__eq%3D2%26source%3Dgllue&savedSearchId=40"

    SELECTORS = {
        "username": [
            "input[name='username']",
            "input[id='username']",
            "input[type='text']",
            "input[name='email']",
            "input[id='email']",
            "input[name='login-email']",
        ],
        "password": [
            "input[name='password']",
            "input[id='password']",
            "input[type='password']",
        ],
        "submit": [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('登录')",
            "button:has-text('Log In')",
            "button:has-text('Sign in')",
        ],
        "candidate_rows": [
            "table tbody tr",
            "table.candidateTable tbody tr",
        ],
        "candidate_link": [
            "a[href*='candidate/detail']",
            "a.detail-link",
        ],
    }

    def __init__(self, username: str, password: str, headless: bool = False, max_candidates: int = 10):
        self.username = username
        self.password = password
        self.headless = headless
        self.max_candidates = max_candidates
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def login(self) -> bool:
        logger.info("🌐 Navigating to login page...")
        await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(1500)

        await self._wait_for_visible_selector(self.SELECTORS["username"], timeout=20000)
        await self._wait_for_visible_selector(self.SELECTORS["password"], timeout=20000)

        username_input = await self._find_first_selector_any_context(self.SELECTORS["username"], visible_only=True)
        password_input = await self._find_first_selector_any_context(self.SELECTORS["password"], visible_only=True)

        if not username_input or not password_input:
            await self._log_available_inputs()
            logger.error("❌ Unable to locate login inputs. Please inspect the login page selectors.")
            return False

        await username_input.fill(self.username)
        await password_input.fill(self.password)
        logger.info("✅ Credentials filled.")

        submit_button = await self._find_first_selector_any_context(self.SELECTORS["submit"], visible_only=True)
        if submit_button:
            await submit_button.click()
        else:
            logger.warning("⚠️ Login button not found, attempting Enter key event.")
            await password_input.press("Enter")

        try:
            await self.page.wait_for_url("**/crm#dashboard*", timeout=30000)
            logger.info("✅ Login successful, dashboard reached.")
            return True
        except TimeoutError:
            logger.error("❌ Login may have failed or requires manual intervention (captcha).")
            return False

    async def fetch_candidates(self, list_url: Optional[str] = None) -> List[CandidateRecord]:
        target_url = list_url or self.DEFAULT_LIST_URL
        logger.info(f"📄 Opening candidate list: {target_url}")
        await self.page.goto(target_url, wait_until="domcontentloaded")

        rows = await self._collect_candidate_rows()
        logger.info(f"📋 Found {len(rows)} rows. Limiting to {self.max_candidates} candidates.")

        records: List[CandidateRecord] = []
        for index, row in enumerate(rows[: self.max_candidates], 1):
            link = await self._find_in_row(row, self.SELECTORS["candidate_link"])
            if not link:
                logger.warning(f"⚠️ Candidate link missing in row {index}, skipping.")
                continue

            href = await link.get_attribute("href")
            if not href:
                logger.warning(f"⚠️ Unable to read candidate URL in row {index}, skipping.")
                continue

            full_url = href if href.startswith("http") else f"https://rpt.gllue.com/{href.lstrip('/') }"
            logger.info(f"🔍 Opening candidate {index}: {full_url}")

            detail_page = await self.context.new_page()
            await detail_page.goto(full_url, wait_until="domcontentloaded")

            record = await self._extract_candidate(detail_page, full_url)
            records.append(record)

            await detail_page.close()
        return records

    async def _extract_candidate(self, page: Page, url: str) -> CandidateRecord:
        name = await self._extract_field(page, ["姓名", "Name"])
        city = await self._extract_field(page, ["所在城市", "城市", "Location"])
        work_experience = await self._extract_work_experience(page)

        logger.info(f"👤 {name or '未命名候选人'} | 城市: {city or '未知'} | 工作经历条目: {len(work_experience)}")
        return CandidateRecord(name=name or "", city=city, work_experience=work_experience, source_url=url)

    async def _extract_field(self, page: Page, labels: List[str]) -> Optional[str]:
        script = """
        (labels) => {
          const rows = Array.from(document.querySelectorAll('tr'));
          for (const row of rows) {
            const cells = Array.from(row.children);
            if (cells.length < 2) continue;
            const label = cells[0].innerText.trim();
            if (labels.some(target => label.includes(target))) {
              return cells[1].innerText.trim();
            }
          }
          const detailItems = Array.from(document.querySelectorAll('[class*="detail"], [class*="info"], [class*="field"]'));
          for (const item of detailItems) {
            const text = item.innerText.trim();
            for (const target of labels) {
              if (text.startsWith(target)) {
                return text.replace(target, '').trim();
              }
            }
          }
          return null;
        }
        """
        try:
            return await page.evaluate(script, labels)
        except Exception:
            return None

    async def _extract_work_experience(self, page: Page) -> List[str]:
        script = """
        () => {
          const experiences = [];
          const sectionCandidates = Array.from(document.querySelectorAll('*')).filter(el => /工作经历|Work Experience/.test(el.textContent || ''));
          let section = null;
          for (const el of sectionCandidates) {
            if (el.querySelector('table') || el.querySelector('tbody')) {
              section = el;
              break;
            }
          }
          if (!section) {
            section = Array.from(sectionCandidates).find(el => el.closest('[data-field="workExperience"]'));
          }
          if (!section) return experiences;

          const rows = Array.from(section.querySelectorAll('tr'));
          for (const row of rows) {
            const cells = Array.from(row.children).map(cell => cell.innerText.trim()).filter(Boolean);
            if (cells.length === 0) continue;
            experiences.push(cells.join(' | '));
          }

          if (experiences.length === 0) {
            const items = Array.from(section.querySelectorAll('li, div, p')).map(el => el.innerText.trim()).filter(Boolean);
            return items;
          }
          return experiences;
        }
        """
        try:
            data = await page.evaluate(script)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    async def _collect_candidate_rows(self) -> List[Page]:
        for selector in self.SELECTORS["candidate_rows"]:
            rows = await self.page.query_selector_all(selector)
            if rows:
                return rows
        return []

    async def _find_first_selector(self, selectors: List[str]):
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    return element
            except Exception:
                continue
        return None

    async def _find_first_selector_any_context(self, selectors: List[str], visible_only: bool = False):
        contexts = [self.page, *self.page.frames]
        for context in contexts:
            for selector in selectors:
                try:
                    element = await context.query_selector(selector)
                    if element:
                        if visible_only:
                            try:
                                if not await element.is_visible():
                                    continue
                            except Exception:
                                continue
                        ctx_url = context.url if hasattr(context, "url") else "frame"
                        logger.debug(f"🔍 Found selector '{selector}' (visible={visible_only}) in context {ctx_url}")
                        return element
                except Exception:
                    continue
        return None

    async def _wait_for_visible_selector(self, selectors: List[str], timeout: int = 15000):
        for selector in selectors:
            try:
                handle = await self.page.wait_for_selector(selector, timeout=timeout, state="visible")
                if handle:
                    return handle
            except TimeoutError:
                continue
            except Exception:
                continue
        return None

    async def _log_available_inputs(self):
        try:
            contexts = [self.page, *self.page.frames]
            for context in contexts:
                ctx_url = context.url if hasattr(context, "url") else "frame"
                inputs = await context.query_selector_all("input")
                logger.info(f"🧭 Context: {ctx_url} | input count: {len(inputs)}")
                for inp in inputs[:10]:
                    name = await inp.get_attribute("name")
                    input_id = await inp.get_attribute("id")
                    input_type = await inp.get_attribute("type")
                    placeholder = await inp.get_attribute("placeholder")
                    logger.info(f"   ↳ input name={name} id={input_id} type={input_type} placeholder={placeholder}")
        except Exception as exc:
            logger.warning(f"⚠️ Unable to log input fields: {exc}")


def save_records(records: List[CandidateRecord], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"gllue_candidates_{timestamp}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(record) for record in records], f, ensure_ascii=False, indent=2)
    logger.info(f"💾 Saved {len(records)} candidate records to {output_path}")
    return output_path


async def main():
    load_dotenv()

    username = os.getenv("GLLUE_USERNAME")
    password = os.getenv("GLLUE_PASSWORD")
    if not username or not password:
        raise RuntimeError("Missing GLLUE_USERNAME or GLLUE_PASSWORD environment variables.")

    headless = os.getenv("GLLUE_HEADLESS", "false").lower() in {"1", "true", "yes"}
    max_candidates = int(os.getenv("GLLUE_MAX_CANDIDATES", "5"))

    async with GllueScraper(username=username, password=password, headless=headless, max_candidates=max_candidates) as scraper:
        logged_in = await scraper.login()
        if not logged_in:
            logger.error("Login failed. Please check credentials or complete captcha manually.")
            return

        records = await scraper.fetch_candidates()
        save_records(records, Path("data"))


if __name__ == "__main__":
    asyncio.run(main())
