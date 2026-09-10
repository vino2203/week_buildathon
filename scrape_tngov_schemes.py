import asyncio
import re
import os
from playwright.async_api import async_playwright

async def main():
    output_dir = "Tamil_nadu_state_schemes"
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        print("Navigating to https://www.tn.gov.in/scheme_list.php?dep_id=Mg== ...")
        await page.goto("https://www.tn.gov.in/scheme_list.php?dep_id=Mg==")
        await page.wait_for_timeout(2000)

        # Get all scheme links for Agriculture Department
        links = await page.locator("a[href*='scheme_details.php?id=']").all()
        
        scheme_urls = set()
        for link in links:
            href = await link.get_attribute("href")
            if href and "scheme_details.php" in href:
                scheme_urls.add("https://www.tn.gov.in/" + href)
        
        print(f"Found {len(scheme_urls)} unique scheme URLs to scrape.")

        for url in scheme_urls:
            print(f"Scraping: {url}")
            try:
                await page.goto(url)
                await page.wait_for_timeout(2000)
                
                # Attempt to get a good title, maybe from the table rows
                # since the page might not have a proper H2 for the scheme title.
                # "Scheme Title/Name:" is usually in a td
                title = "Unknown Scheme"
                tds = await page.locator("td").all()
                for i, td in enumerate(tds):
                    text = await td.inner_text()
                    if "Scheme Title/Name" in text and i + 1 < len(tds):
                        title = await tds[i+1].inner_text()
                        break
                
                if title == "Unknown Scheme":
                    title = await page.title()
                
                safe_filename = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip()
                if not safe_filename:
                    safe_filename = url.strip('/').split('=')[-1]
                
                # Get the page contents
                content_elem = page.locator(".scheme_det").first
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
