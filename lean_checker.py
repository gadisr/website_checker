#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from bs4 import BeautifulSoup

URL = "https://www.leaan.co.il/category/%D7%A1%D7%A4%D7%95%D7%A8%D7%98/%D7%9B%D7%93%D7%95%D7%A8%D7%92%D7%9C/%D7%94%D7%A4%D7%95%D7%A2%D7%9C-%D7%A4%D7%AA%D7%97-%D7%AA%D7%A7%D7%95%D7%94"

# ntfy configuration:
#  - NTFY_TOPIC is provided via GitHub Actions secret
#  - Optional NTFY_BASE_URL (defaults to https://ntfy.sh)
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
NTFY_BASE_URL = os.environ.get("NTFY_BASE_URL", "https://ntfy.sh").rstrip("/")


def count_items(html: str) -> int:
    """
    Count how many upcoming games ('משחקים קרובים') exist on the page.

    Strategy:
      1. Find the section whose heading contains 'משחקים קרובים'
      2. Inside it, count links containing 'לפרטים נוספים'
      3. Fallback: count 'לפרטים נוספים' in full HTML
      4. If 'There are no upcoming games' text appears, force count=0
    """
    soup = BeautifulSoup(html, "html.parser")

    section = None
    for tag in soup.find_all(["h2", "h3"]):
        if "משחקים קרובים" in tag.get_text(strip=True):
            section = tag.parent
            break

    if section:
        links = [
            a for a in section.find_all("a")
            if "לפרטים נוספים" in a.get_text(strip=True)
        ]
        count = len(links)
    else:
        count = html.count("לפרטים נוספים")

    if "There are no upcoming games" in html:
        count = 0

    return count


def notify(message: str) -> None:
    """
    Send a push notification via ntfy.
    You must have the ntfy app installed and subscribed to the topic.
    """
    if not NTFY_TOPIC:
        raise RuntimeError("NTFY_TOPIC environment variable is not set")

    url = f"{NTFY_BASE_URL}/{NTFY_TOPIC}"
    resp = requests.post(
        url,
        data=message.encode("utf-8"),
        headers={
            "Title": "Leaan – הפועל פ\"ת",
            "Tags": "soccer,ticket,alert",
        },
        timeout=15,
    )
    resp.raise_for_status()


def main() -> None:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; leaan-hpt-checker/1.0)",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    resp = requests.get(URL, headers=headers, timeout=20)
    resp.raise_for_status()

    html = resp.text
    count = count_items(html)

    # Condition: exactly 2 items
    if count == 2:
        msg = (
            f"שלום,\n\n"
            f"בעמוד של הפועל פתח תקוה יש כרגע בדיוק {count} משחקים ברשימת 'משחקים קרובים'.\n"
            f"עמוד: {URL}\n\n"
            f"👀 בדוק אם יש כרטיסים זמינים."
        )
        notify(msg)


if __name__ == "__main__":
    main()
