import asyncio
import random
import re
from playwright.async_api import async_playwright

TARGET_NAMES = ["larper siêu bá khí"]
TEMPLATE = "{Chuỗi|chuoi|Tin nhắn này để giữ chuỗi.}! {Chúc ngày mới vui vẻ|Rất vui được kết nối|Tuần mới thuận lợi}!"
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
        
        await page.goto("https://www.tiktok.com/messages", wait_until="domcontentloaded")
        await asyncio.sleep(5)

        chat_input = page.locator('div[contenteditable="true"], [data-e2e="chat-input"]').first

        for name in TARGET_NAMES:
            try:
                # 1. Click vào đoạn chat theo tên hiển thị
                await page.locator(f':text-is("{name}"), [data-e2e="inbox-title"]:has-text("{name}")').last.click()
                
                # 2. Nhập và gửi tin nhắn
                await chat_input.wait_for(state="visible", timeout=6000)
                await chat_input.fill(spin_text(TEMPLATE))
                await page.keyboard.press("Enter")
                print(f"[✓] Đã gửi tới: {name}")

            except Exception as e:
                print(f"[!] Lỗi với {name}: {e}")

            await asyncio.sleep(random.uniform(10.0, 20.0))

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())