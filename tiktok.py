import asyncio
import os
import random
import re
from playwright.async_api import async_playwright

# Replace with the exact display name of the chat recipient
TARGET_NAMES = ["DISPLAY_NAME"]

# Template messages to randomly pick from
TEMPLATE = "{Text A|Text B|Text C}!"

# Folder to store your persistent login profile locally
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, "tiktok_browser_profile")


def spin_text(text: str) -> str:
    return re.sub(
        r"\{([^{}]+)\}", lambda m: random.choice(m.group(1).split("|")), text
    )


async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("[*] Navigating to TikTok Messages...")
        await page.goto(
            "https://www.tiktok.com/messages", wait_until="domcontentloaded"
        )

        print("[*] Waiting for inbox interface to load...")
        await asyncio.sleep(6)

        if "login" in page.url:
            print(
                "\n[!] ACTION REQUIRED: Please log into TikTok manually in the browser window."
            )
            print("[*] Waiting up to 120 seconds for you to log in...")
            try:
                await page.wait_for_url(
                    "https://www.tiktok.com/messages**", timeout=120000
                )
                print(
                    "[✓] Login detected! Saved to profile for future runs.\n"
                )
            except Exception:
                print(
                    "[!] Login timed out. Please run the script again and log in."
                )
                await context.close()
                return

        chat_input = page.locator(
            'div[contenteditable="true"], [data-e2e="chat-input"]'
        ).first

        for name in TARGET_NAMES:
            print(f'\n[+] Processing: "{name}"')
            try:
                chat_row = page.locator(
                    f':text-is("{name}"), [data-e2e="inbox-title"]:has-text("{name}")'
                ).last
                await chat_row.click()

                await chat_input.wait_for(state="visible", timeout=8000)
                message = spin_text(TEMPLATE)
                print(f'[>] Sending: "{message}"')

                await chat_input.fill(message)
                await page.keyboard.press("Enter")
                print(f'[✓] Successfully sent to "{name}"!')

            except Exception as e:
                print(f'[!] Error processing "{name}": {e}')

            delay_time = random.uniform(5.0, 10.0)
            await asyncio.sleep(delay_time)

        print("\n[+] Done!")
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
