#!/usr/bin/env python3
"""
Facebook Group Invite Automation
Automates the process of inviting Facebook friends to join a group.
Project by SoClose Society — https://soclose.com

Usage:
    python main.py [--group-url URL] [--lang fr|en] [--batch-size MIN MAX]
                   [--max-invites N] [--headless]

Disclaimer: Educational purposes only. Use at your own risk.
License: MIT
"""

import argparse
import logging
import os
import re
import signal
import sys
import time
import random

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException,
)

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("fb_invite")

# ---------------------------------------------------------------------------
# Multi-language labels
# ---------------------------------------------------------------------------
LABELS = {
    "fr": {
        "invite_button": "Inviter",
        "invite_friends_menu": "Inviter des amis Facebook",
        "invite_dialog": "Invitez des amis à rejoindre ce groupe",
        "send_invitations": "Envoyer les invitations",
        "friends_selected_suffix": "AMIS SÉLECTIONNÉS",
    },
    "en": {
        "invite_button": "Invite",
        "invite_friends_menu": "Invite Facebook friends",
        "invite_dialog": "Invite friends to join this group",
        "send_invitations": "Send invitations",
        "friends_selected_suffix": "FRIENDS SELECTED",
    },
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_LANG = "fr"
DEFAULT_BATCH_MIN = 5
DEFAULT_BATCH_MAX = 10
DEFAULT_MAX_INVITES = 0  # 0 = unlimited
RETRY_LIMIT = 10
ELEMENT_WAIT_TIMEOUT = 15  # seconds
POST_INVITE_DELAY = 6  # seconds

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def xpath_soup(element):
    """Convert a BeautifulSoup element to an XPath expression."""
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name
            if siblings == [child]
            else "%s[%d]" % (child.name, 1 + siblings.index(child))
        )
        child = parent
    components.reverse()
    return "/%s" % "/".join(components)


def validate_facebook_group_url(url: str) -> bool:
    """Return True if *url* looks like a valid Facebook group URL."""
    pattern = r"^https?://(www\.|m\.)?facebook\.com/groups/.+"
    return bool(re.match(pattern, url))


def find_element_with_retry(driver, soup_finder, click=False, retries=RETRY_LIMIT):
    """
    Re-parse the page up to *retries* times looking for an element via
    *soup_finder(soup)* -> BeautifulSoup element | None.
    If *click* is True the element is also clicked via Selenium.
    Returns the BS element or None.
    """
    for attempt in range(1, retries + 1):
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        element = soup_finder(soup)
        if element is not None:
            if click:
                try:
                    sel_el = driver.find_element(By.XPATH, xpath_soup(element))
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", sel_el)
                    time.sleep(0.3)
                    sel_el.click()
                except (ElementClickInterceptedException, StaleElementReferenceException) as exc:
                    logger.warning("Click attempt %d failed: %s", attempt, exc)
                    time.sleep(1)
                    continue
            return element
        logger.debug("Attempt %d/%d – element not found, retrying…", attempt, retries)
        time.sleep(1)
    return None


def refresh_friend_list(driver, labels):
    """Re-parse the invitation dialog and return the friend-item list."""
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    dialog = soup.find("div", attrs={"aria-label": labels["invite_dialog"]})
    if dialog is None:
        return [], soup
    items = dialog.find_all(
        "div", attrs={"style": re.compile(r"padding-left:\s*8px.*padding-right:\s*8px")}
    )
    return items, soup


def get_selected_count(driver, labels):
    """Parse the 'N FRIENDS SELECTED' text and return N as int."""
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    dialog = soup.find("div", attrs={"aria-label": labels["invite_dialog"]})
    if dialog is None:
        return 0
    spans = dialog.find_all("span", attrs={"dir": "auto"})
    for span in spans:
        text = span.get_text(strip=True)
        if labels["friends_selected_suffix"] in text.upper():
            parts = text.split()
            try:
                return int(parts[0])
            except (ValueError, IndexError):
                pass
    return 0

# ---------------------------------------------------------------------------
# Core automation
# ---------------------------------------------------------------------------

class FacebookGroupInviter:
    """Encapsulates the full invite-automation workflow."""

    def __init__(self, group_url, lang=DEFAULT_LANG, batch_min=DEFAULT_BATCH_MIN,
                 batch_max=DEFAULT_BATCH_MAX, max_invites=DEFAULT_MAX_INVITES,
                 headless=False):
        self.group_url = group_url
        self.lang = lang
        self.labels = LABELS[lang]
        self.batch_min = batch_min
        self.batch_max = batch_max
        self.max_invites = max_invites
        self.headless = headless
        self.total_invited = 0
        self.driver = None
        self._shutdown = False

        # Graceful shutdown on Ctrl-C
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.info("Shutdown signal received. Finishing current batch…")
        self._shutdown = True

    # ------------------------------------------------------------------
    # Browser setup
    # ------------------------------------------------------------------
    def start_browser(self):
        """Initialize Chrome WebDriver."""
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-notifications")
        if self.headless:
            options.add_argument("--headless=new")

        if ChromeDriverManager is not None:
            service = Service(ChromeDriverManager().install())
        else:
            service = Service()

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.maximize_window()
        logger.info("Browser started.")

    def navigate_to_facebook(self):
        """Open Facebook so the user can log in."""
        self.driver.get("https://www.facebook.com/")
        logger.info("Navigated to Facebook. Please log in manually in the browser.")

    def quit(self):
        """Close the browser cleanly."""
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
            logger.info("Browser closed.")

    # ------------------------------------------------------------------
    # Invite workflow
    # ------------------------------------------------------------------
    def _click_invite_button(self):
        """Find and click the main 'Invite' button on the group page."""
        def finder(soup):
            buttons = soup.find_all("div", attrs={"role": "button"})
            for btn in buttons:
                aria = btn.attrs.get("aria-label", "")
                if self.labels["invite_button"] in aria:
                    return btn
            return None

        el = find_element_with_retry(self.driver, finder, click=True)
        if el is None:
            raise RuntimeError("Could not find the 'Invite' button on the group page.")
        logger.info("Clicked the 'Invite' button.")

    def _click_invite_friends_menu(self):
        """Click the 'Invite Facebook friends' menu item."""
        def finder(soup):
            items = soup.find_all("div", attrs={"role": "menuitem"})
            for item in items:
                if self.labels["invite_friends_menu"] in item.get_text():
                    return item
            return None

        el = find_element_with_retry(self.driver, finder, click=True)
        if el is None:
            raise RuntimeError("Could not find the 'Invite Facebook friends' menu item.")
        logger.info("Clicked 'Invite Facebook friends' menu.")

    def _wait_for_dialog(self):
        """Wait for the invitation dialog to appear."""
        def finder(soup):
            return soup.find("div", attrs={"aria-label": self.labels["invite_dialog"]})

        el = find_element_with_retry(self.driver, finder, click=False)
        if el is None:
            raise RuntimeError("Invitation dialog did not appear.")
        logger.info("Invitation dialog is open.")

    def _select_friends(self, target_count):
        """Select up to *target_count* friends from the dialog."""
        selected = 0
        idx = 0
        consecutive_errors = 0

        while selected < target_count and not self._shutdown:
            friends, _ = refresh_friend_list(self.driver, self.labels)
            if idx >= len(friends):
                logger.info("Reached end of visible friends list (%d items).", len(friends))
                break

            friend_el = friends[idx]

            # Only click if there's a checkbox (friend not yet invited)
            if not friend_el.find("div", attrs={"role": "checkbox"}):
                idx += 1
                continue

            try:
                xpath = xpath_soup(friend_el)
                sel_el = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'})", sel_el
                )
                time.sleep(0.3)
                sel_el.click()
                selected += 1
                consecutive_errors = 0
                logger.info(
                    "Selected friend %d/%d (index %d)",
                    selected,
                    target_count,
                    idx,
                )
            except (
                NoSuchElementException,
                StaleElementReferenceException,
                ElementClickInterceptedException,
            ) as exc:
                consecutive_errors += 1
                logger.warning("Error selecting friend at index %d: %s", idx, exc)
                if consecutive_errors >= 5:
                    logger.error("Too many consecutive errors, stopping selection.")
                    break

            idx += 1
            time.sleep(0.5)

        return selected

    def _send_invitations(self):
        """Click the 'Send invitations' button."""
        def finder(soup):
            return soup.find("div", attrs={"aria-label": self.labels["send_invitations"]})

        el = find_element_with_retry(self.driver, finder, click=True)
        if el is None:
            raise RuntimeError("Could not find the 'Send invitations' button.")
        logger.info("Clicked 'Send invitations'.")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        """Execute the full invitation loop."""
        batch_number = 0

        while not self._shutdown:
            batch_number += 1
            batch_size = random.randint(self.batch_min, self.batch_max)
            logger.info(
                "=== Batch #%d — targeting %d friends ===",
                batch_number,
                batch_size,
            )

            try:
                # Navigate to group
                self.driver.get(self.group_url)
                time.sleep(2)

                # Open invite flow
                self._click_invite_button()
                time.sleep(1)
                self._click_invite_friends_menu()
                self._wait_for_dialog()

                # Select friends
                selected = self._select_friends(batch_size)
                confirmed = get_selected_count(self.driver, self.labels)
                logger.info(
                    "Batch #%d: clicked %d, confirmed selected = %d",
                    batch_number,
                    selected,
                    confirmed,
                )

                if confirmed == 0:
                    logger.info("No friends left to invite. Stopping.")
                    break

                # Send
                self._send_invitations()
                self.total_invited += confirmed
                logger.info(
                    "Batch #%d sent. Total invited so far: %d",
                    batch_number,
                    self.total_invited,
                )

                # Check max invites limit
                if self.max_invites > 0 and self.total_invited >= self.max_invites:
                    logger.info(
                        "Reached max invites limit (%d). Stopping.",
                        self.max_invites,
                    )
                    break

                # Delay between batches
                logger.info("Waiting %ds before next batch…", POST_INVITE_DELAY)
                time.sleep(POST_INVITE_DELAY)

            except RuntimeError as exc:
                logger.error("Batch #%d failed: %s", batch_number, exc)
                logger.info("Retrying in 5 seconds…")
                time.sleep(5)
            except WebDriverException as exc:
                logger.error("Browser error during batch #%d: %s", batch_number, exc)
                break

        logger.info("Finished. Total friends invited: %d", self.total_invited)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Facebook Group Invite Automation — SoClose Society",
        epilog="More info: https://soclose.com",
    )
    parser.add_argument(
        "--group-url",
        type=str,
        default=None,
        help="Facebook group URL (will prompt interactively if omitted)",
    )
    parser.add_argument(
        "--lang",
        choices=LABELS.keys(),
        default=DEFAULT_LANG,
        help="Facebook UI language (default: fr)",
    )
    parser.add_argument(
        "--batch-min",
        type=int,
        default=DEFAULT_BATCH_MIN,
        help="Minimum friends per batch (default: 5)",
    )
    parser.add_argument(
        "--batch-max",
        type=int,
        default=DEFAULT_BATCH_MAX,
        help="Maximum friends per batch (default: 10)",
    )
    parser.add_argument(
        "--max-invites",
        type=int,
        default=DEFAULT_MAX_INVITES,
        help="Stop after N invites total (0 = unlimited, default: 0)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode (login will not be possible interactively)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get group URL
    group_url = args.group_url
    if not group_url:
        group_url = input("Enter the Facebook group URL: ").strip()

    if not validate_facebook_group_url(group_url):
        logger.error("Invalid Facebook group URL: %s", group_url)
        logger.error("Expected format: https://www.facebook.com/groups/YOUR_GROUP")
        sys.exit(1)

    # Create inviter
    inviter = FacebookGroupInviter(
        group_url=group_url,
        lang=args.lang,
        batch_min=args.batch_min,
        batch_max=args.batch_max,
        max_invites=args.max_invites,
        headless=args.headless,
    )

    try:
        inviter.start_browser()
        inviter.navigate_to_facebook()

        input('\nLog in to Facebook in the browser, then press Enter to start…')

        inviter.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        inviter.quit()


if __name__ == "__main__":
    main()
