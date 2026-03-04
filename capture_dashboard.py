import asyncio
import os
from playwright.async_api import async_playwright

async def capture_responsive():
    base_dir = "dashboard_screenshots"
    viewports = [
        {"name": "desktop", "width": 1920, "height": 1080},
        {"name": "tablet", "width": 768, "height": 1024},
        {"name": "mobile", "width": 375, "height": 812}
    ]
    
    # Final Professionally Labeled Tab IDs
    tabs = ["pillars", "impact", "taxonomy", "software"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for vp in viewports:
            print(f"[*] Processing {vp['name']} viewport ({vp['width']}x{vp['height']})")
            vp_dir = os.path.join(base_dir, vp['name'])
            os.makedirs(vp_dir, exist_ok=True)
            context = await browser.new_context(viewport={'width': vp['width'], 'height': vp['height']})
            page = await context.new_page()
            file_path = "file://" + os.path.abspath("gdelt_openalex_dashboard.html")
            await page.goto(file_path)
            await asyncio.sleep(2)
            for tab_id in tabs:
                print(f"    - Capturing tab: {tab_id}")
                await page.evaluate(f"tab('{tab_id}')")
                await asyncio.sleep(1.5)
                await page.screenshot(path=os.path.join(vp_dir, f"{tab_id}.png"), full_page=True)
            await context.close()
        await browser.close()
    print("[SUCCESS] All responsive screenshots saved.")

if __name__ == "__main__":
    asyncio.run(capture_responsive())
