#!/usr/bin/env python3
"""Watches a campus portal for grade changes and notifies over Telegram."""
import os
import json
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

load_dotenv()

def require(key: str) -> str:
    v = os.getenv(key)
    if not v:
        raise SystemExit(f"Missing '{key}' in your .env file")
    return v


USER       = require("MYCAMPUS_USER")
PASS       = require("MYCAMPUS_PASS")
TG_TOKEN   = require("TG_TOKEN")
TG_CHAT_ID = require("TG_CHAT_ID")
USER_AGENT = require("USER_AGENT")

BASE   = require("MYCAMPUS_BASE").rstrip("/") + "/"
TENANT = require("MYCAMPUS_TENANT")
TILE   = require("GRADES_TILE")
XHR    = require("GRADES_XHR")

REJECT  = [m.strip() for m in os.getenv("REJECT_MARKERS", "").split(",") if m.strip()]
COOKIES = json.loads(os.getenv("BOOTSTRAP_COOKIES", "{}"))

_url      = urlparse(BASE)
DOMAIN    = _url.hostname
ORIGIN    = f"{_url.scheme}://{_url.netloc}"
LOGIN_URL = BASE + "login"

HEADLESS   = os.getenv("HEADLESS", "1") != "0"
STATE_FILE = Path(__file__).parent / "last_state.json"


def telegram(text: str) -> None:
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT_ID, "text": text},
        timeout=30,
    )
    r.raise_for_status()


def login() -> requests.Session:
    s = requests.Session()
    for name, value in COOKIES.items():
        s.cookies.set(name, value, domain=DOMAIN)
    headers = {"content-type": "application/x-www-form-urlencoded",
               "origin": ORIGIN, "referer": BASE, "user-agent": USER_AGENT}
    payload = {"tenant": TENANT, "username": USER, "password": PASS,
               "sso": "", "href": BASE}
    s.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=False, timeout=30)
    if "JSESSIONID" not in s.cookies.get_dict():
        raise SystemExit("Login failed (no JSESSIONID) — check credentials in .env.")
    s.get(BASE, headers={"user-agent": USER_AGENT}, timeout=30)
    print("Login OK — JSESSIONID acquired.")
    return s


def to_playwright_cookies(session: requests.Session):
    return [{"name": c.name, "value": c.value or "",
             "domain": DOMAIN, "path": c.path or "/"}
            for c in session.cookies]


def fetch_grades_html(session: requests.Session) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(user_agent=USER_AGENT)
        context.add_cookies(to_playwright_cookies(session))
        page = context.new_page()

        page.goto(BASE, wait_until="domcontentloaded")

        def is_data(resp):
            return XHR in resp.url and resp.request.resource_type in ("fetch", "xhr")

        tile = page.locator(TILE).first
        shot = str(Path(__file__).parent / "debug.png")

        try:
            tile.wait_for(state="visible", timeout=45000)
        except PWTimeout:
            page.screenshot(path=shot)
            browser.close()
            raise SystemExit(
                f"The grades tile never appeared. See {shot}. If it shows a login "
                "page, the cookie injection failed; if it shows the portal but no "
                "matching tile, fix GRADES_TILE in your .env.")

        html = ""
        try:
            with page.expect_response(is_data, timeout=45000) as info:
                tile.click()
            html = info.value.text()
        except PWTimeout:
            page.screenshot(path=shot)
            page.wait_for_timeout(2000)
            html = page.content()
            print(f"(clicked, but no data response intercepted — see {shot})")

        browser.close()
        return html


def extract_text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)


def load_previous() -> str:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("grades", "")
    return ""


def save(text: str) -> None:
    STATE_FILE.write_text(
        json.dumps({"grades": text}, ensure_ascii=False), encoding="utf-8"
    )


def main():
    session = login()
    html = fetch_grades_html(session)
    current = extract_text(html)

    if not current.strip() or any(m in html for m in REJECT):
        raise SystemExit("Fetch looked wrong (empty or incomplete) — not saving.")

    previous = load_previous()

    if not previous:
        save(current)
        print("Baseline saved. Will notify on future changes.")
        return

    if current != previous:
        old_lines = set(previous.splitlines())
        added = [l for l in current.splitlines() if l and l not in old_lines]
        detail = "\n".join(added[:30]) if added else "(grades page changed)"
        telegram("MyCampus update — something changed:\n\n" + detail)
        save(current)
        print("Change detected -> Telegram sent.")
    else:
        print("No change.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        try:
            telegram(f"Grade watcher crashed: {e}")
        except Exception:
            pass
        print(f"Error: {e}")
        raise
