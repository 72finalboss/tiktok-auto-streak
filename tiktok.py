import os
import asyncio
import random
import re
from playwright.async_api import async_playwright

# Change DISPLAY_NAME to the display name of the profile you want to chat with
TARGET_NAMES = ["DISPLAY_NAME"]

# Template messages to pick from
TEMPLATE = "{Text A|Text B|Text C}!"

def spin_text(text: str) -> str:
    return re.sub(r'\{([^{}]+)\}', lambda m: random.choice(m.group(1).split('|')), text)

async def main():
    # 1. Rebuild auth.json from GitHub Secrets if running in the cloud
    auth_secret = os.environ.get("TIKTOK_AUTH_JSON")
    storage_state = None

    if auth_secret:
        with open("auth.json", "w", encoding="utf-8") as f:
            f.write(auth_secret)
        storage_state = "auth.json"
    elif os.path.exists("auth.json"):
        storage_state = "auth.json"

    async with async_playwright() as p:
        # 2. Launch browser in headless mode (headless=True is required for GitHub Actions)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

        # 3. Create context using the saved login state
        context = await browser.new_context(
            storage_state=storage_state,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("[*] Navigating to TikTok Messages...")
        await page.goto("https://www.tiktok.com/messages", wait_until="networkidle")

        # 4. Check if session was accepted or rejected
        if "login" in page.url:
            print("[!] Error: Redirected to login page. Session expired or missing cookies.")
            await browser.close()
            return

        chat_input = page.locator('div[contenteditable="true"], [data-e2e="chat-input"]').first

        for name in TARGET_NAMES:
            print(f"\n[+] Processing: \"{name}\"")
            try:
                # Click target chat by display name
                chat_row = page.locator(f':text-is("{name}"), [data-e2e="inbox-title"]:has-text("{name}")').last
                await chat_row.click()

                # Wait for input box, generate message, and send
                await chat_input.wait_for(state="visible", timeout=8000)
                message = spin_text(TEMPLATE)
                print(f"[>] Sending: \"{message}\"")

                await chat_input.fill(message)
                await page.keyboard.press("Enter")
                print(f"[✓] Successfully sent to \"{name}\"!")

            except Exception as e:
                print(f"[!] Error processing \"{name}\": {e}")

            delay_time = random.uniform(5.0, 10.0)
            await asyncio.sleep(delay_time)

        print("\n[+] All targets processed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
