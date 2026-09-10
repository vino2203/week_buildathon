import asyncio
import re
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        # Ensure output directory exists
        output_dir = "Tamil_nadu_state_schemes"
        os.makedirs(output_dir, exist_ok=True)

        # Navigate to the target URL
        await page.goto("https://www.tnagrisnet.tn.gov.in/people_app/GoScheme")
        
        # Wait for the table to be visible
        await page.wait_for_selector("#table tbody tr")
        
        total_pages = 6
        
        for page_num in range(1, total_pages + 1):
            print(f"--- Scraping Page {page_num} ---")
            
            # Wait for rows to load
            await page.wait_for_selector("#table tbody tr")
            await page.wait_for_timeout(2000) # Give data table some time to render
            
            rows = await page.locator("#table tbody tr").all()
            
            for i in range(len(rows)):
                # Re-fetch rows in case DOM changed
                current_rows = await page.locator("#table tbody tr").all()
                if i >= len(current_rows):
                    break
                    
                row = current_rows[i]
                
                # Assuming the link is in the 3rd column (index 2) "Scheme" or 2nd column
                # The user mentioned "2nd row" but likely meant "2nd column" or the link inside the row
                cells = await row.locator("td").all()
                if len(cells) < 3:
                    continue
                
                # Get the scheme name from the cells, fallback to link text
                scheme_name_text = await cells[2].inner_text()
                link = row.locator("a").first
                
                if await link.count() > 0:
                    link_text = await link.inner_text()
                    scheme_name = link_text.strip()
                else:
                    scheme_name = scheme_name_text.strip()
                
                # Clean up file name
                safe_filename = re.sub(r'[^a-zA-Z0-9_\- ]', '', scheme_name).strip()
                
                # If tester, skip
                if "tester" in scheme_name.lower() or "test" in scheme_name.lower():
                    print(f"Skipping tester scheme: {scheme_name}")
                    continue
                    
                print(f"Scraping scheme: {scheme_name}")
                
                # Click the link to open popup
                if await link.count() > 0:
                    await link.click(force=True)
                else:
                    print("No link found in row, skipping.")
                    continue
                
                # Wait for the modal/popup to appear. 
                # From the page source, it seems there's a dialog like #zoom_det or a modal
                try:
                    # Wait for a generic dialog/modal class or the specific id found in source
                    # Adjust the selector based on actual popup ID if needed
                    await page.locator(".ui-dialog:visible, .modal:visible").first.wait_for(timeout=5000)
                    
                    # Extract data from popup
                    popup_content = await page.locator(".ui-dialog:visible, .modal:visible").first.inner_text()
                    
                    # Save to file
                    file_path = os.path.join(output_dir, f"{safe_filename}.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(popup_content)
                    print(f"Saved: {file_path}")
                    
                    # Close popup (clicking the close button)
                    close_btn = page.locator(".ui-dialog-titlebar-close, .modal-header .close, button:has-text('Close')").first
                    if await close_btn.count() > 0 and await close_btn.is_visible():
                        await close_btn.click(force=True)
                    else:
                        # Press Escape if no close button found
                        await page.keyboard.press("Escape")
                        
                    # Wait for popup to close
                    await page.wait_for_timeout(1000)
                    
                    # Force hide dialogs and overlays just in case
                    await page.evaluate("document.querySelectorAll('.ui-dialog, .ui-widget-overlay, .modal-backdrop').forEach(el => el.style.display = 'none')")
                    
                except Exception as e:
                    print(f"Could not scrape popup for {scheme_name}: {e}")
                    # Try to close anyway
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(1000)
                    await page.evaluate("document.querySelectorAll('.ui-dialog, .ui-widget-overlay, .modal-backdrop').forEach(el => el.style.display = 'none')")
                    
            # Go to next page if not the last page
            if page_num < total_pages:
                # The next button is often an <li> containing an <a>
                next_button_parent = page.locator(".paginate_button.next").first
                
                if await next_button_parent.count() > 0 and not await next_button_parent.evaluate("el => el.classList.contains('disabled')"):
                    next_link = next_button_parent.locator("a").first
                    if await next_link.count() > 0:
                        await next_link.click(force=True)
                    else:
                        await next_button_parent.click(force=True)
                    
                    # Wait for the table to refresh
                    await page.wait_for_timeout(3000)
                else:
                    print("Next button not found or disabled, stopping pagination.")
                    break

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
