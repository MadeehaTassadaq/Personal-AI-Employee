#!/usr/bin/env python3
"""
WhatsApp Session Setup Script
Run this to scan QR code and establish WhatsApp session.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ['WHATSAPP_SESSION_PATH'] = str(project_root / 'credentials' / 'whatsapp_session')
os.environ['WHATSAPP_HEADLESS'] = 'false'  # Show browser for QR scan

async def main():
    from playwright.async_api import async_playwright

    session_path = project_root / 'credentials' / 'whatsapp_session'
    session_path.mkdir(parents=True, exist_ok=True)

    # Remove stale lock files
    lock_file = session_path / 'SingletonLock'
    if lock_file.exists():
        lock_file.unlink()
        print("Removed stale lock file.")

    print("Starting WhatsApp Web...")
    print(f"Session path: {session_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        page = await browser.new_page()
        await page.goto('https://web.whatsapp.com', timeout=120000)

        # Check if already logged in (session exists)
        try:
            await page.wait_for_selector('[data-testid="chat-list"]', timeout=15000)
            print("\n" + "="*50)
            print("SESSION FOUND - Already logged in!")
            print("Closing browser in 3 seconds...")
            print("="*50 + "\n")
            await page.wait_for_timeout(3000)
        except:
            # Need QR code scan
            print("\n" + "="*50)
            print("SCAN THE QR CODE WITH YOUR PHONE")
            print("Once logged in, wait for chats to load, then close the browser.")
            print("="*50 + "\n")

            # Wait for user to close browser or login
            try:
                await page.wait_for_selector('[data-testid="chat-list"]', timeout=300000)
                print("Login successful! Closing in 3 seconds...")
                await page.wait_for_timeout(3000)
            except:
                pass

        await browser.close()

    print("\nSession saved! WhatsApp MCP server is ready to use.")

if __name__ == '__main__':
    asyncio.run(main())
