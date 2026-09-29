import asyncio
from backend.config import TN_SCHEMES_DIR
import re
import os
from playwright.async_api import async_playwright

async def main():
    output_dir = TN_SCHEMES_DIR
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        print("Navigating to https://aed.tn.gov.in/en/ ...")
        await page.goto("https://aed.tn.gov.in/en/")
        await page.wait_for_timeout(2000)

        # Get all scheme links from the navigation/dropdowns
        # The links should contain "/en/schemes/" in their href
        links = await page.locator("a[href*='/en/schemes/']").all()
        
        scheme_urls = set()
        for link in links:
            href = await link.get_attribute("href")
            if href and href.startswith("/en/schemes/"):
                scheme_urls.add("https://aed.tn.gov.in" + href)
        
        print(f"Found {len(scheme_urls)} unique scheme URLs to scrape.")

        for url in scheme_urls:
            print(f"Scraping: {url}")
            try:
                await page.goto(url)
                await page.wait_for_timeout(2000)
                
                # Get the title (h2 inside .page-contents or fallback to page title)
                title_elem = page.locator(".page-contents h2").first
                if await title_elem.count() > 0:
                    title = await title_elem.inner_text()
                else:
                    title = await page.title()
                
                safe_filename = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip()
                if not safe_filename:
                    # fallback if regex clears out everything
                    safe_filename = url.strip('/').split('/')[-1]
                
                # Get the page contents
                content_elem = page.locator(".page-contents").first
                if await content_elem.count() > 0:
                    content_text = await content_elem.inner_text()
                else:
                    content_text = await page.locator("body").inner_text()
                
                file_path = os.path.join(output_dir, f"{safe_filename}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content_text)
                    
                print(f"Saved: {file_path}")
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
