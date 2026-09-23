import asyncio
import random
import re
from playwright.async_api import async_playwright

#Change DISPLAY_NAME to the display name of the profile you wanna chat with
TARGET_NAMES = ["DISPLAY_NAME"]
#Insert your desired text into text A, B, C
#The program will randomly choose between A, B, C to send
#Add more | if you want more text options
TEMPLATE = "{Text A|Text B|Text C}!"
USER_DATA_DIR = "./tiktok_browser_profile"

def spin_text(text: str) -> str:
    return re.sub(r'\{([^{}]+)\}', lambda m: random.choice(m.group(1).split('|')), text)

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("[*] Navigating to TikTok Messages...")
        await page.goto("https://www.tiktok.com/messages", wait_until="domcontentloaded")

        print("[*] Waiting 5 seconds for the inbox interface to load...")
        await asyncio.sleep(5)

        chat_input = page.locator('div[contenteditable="true"], [data-e2e="chat-input"]').first

        for name in TARGET_NAMES:
            print(f"\n[+] Processing: \"{name}\"")
            try:
                # 1. Click target chat by display name
                chat_row = page.locator(f':text-is("{name}"), [data-e2e="inbox-title"]:has-text("{name}")').last
                await chat_row.click()

                # 2. Wait for input, spin text, and send
                await chat_input.wait_for(state="visible", timeout=6000)
                message = spin_text(TEMPLATE)
                print(f"[>] Sending: \"{message}\"")

                await chat_input.fill(message)
                await page.keyboard.press("Enter")
                print(f"[✓] Successfully sent to \"{name}\"!")

            except Exception as e:
                print(f"[!] Error processing \"{name}\": {e}")

            delay_time = random.uniform(10.0, 20.0)
            print(f"[*] Sleeping for {delay_time:.1f}s before next contact...")
            await asyncio.sleep(delay_time)

        print("\n[+] All targets have been processed successfully!")
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
