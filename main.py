# SAFE SKELETON: log in manually beforehand; at T-0 just open the event page.
# pip install selenium webdriver-manager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time, logging, pathlib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

IKKE_MEDLEM_QTY = 9
MEDLEM_QTY = 4
EMAIL = "jakobildstad@gmail.com"
DROP_TIME = "2025-08-12T13:59:58+02:00" # 2 seconds before 14:00
DROP_URL = "https://www.samfundet.no/arrangement/4596-toga-hele-huset" # Event URL

def open_event_when_live(url: str, onsale_iso: str, chrome_profile_dir: str | None = None):
    """Opens the event page exactly at on-sale time using your persistent Chrome profile.
    Automates the purchasing process up to the payment step."""
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)   # keep Chrome open after Python exits

    if chrome_profile_dir:
        p = pathlib.Path(chrome_profile_dir).expanduser()
        options.add_argument(f"--user-data-dir={p}")     # keep cookies/session
        options.add_argument("--profile-directory=Default")
    driver = None

    try:
        logging.info("Launching Chrome…")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    except Exception as e:
        logging.exception("Failed to start Chrome/Driver:", e)
        return
    
    wait = WebDriverWait(driver, 20)  # Increased back to 20 for form elements
    # Wait until T-0 with high-resolution sleep
    target = datetime.fromisoformat(onsale_iso).astimezone(ZoneInfo("Europe/Oslo"))
    while True:
        now = datetime.now(ZoneInfo("Europe/Oslo"))
        if now >= target: break
        time.sleep(min(0.1, (target - now).total_seconds()))
    driver.get(url)

    logging.info("Opened event page at T-0.")
    
    # Automated purchasing up to payment step
    try:
        # 1) AGGRESSIVE buy button hunting - retry every 0.5 seconds for 30 seconds
        button_found = False
        max_attempts = 60  # 60 attempts x 0.5 seconds = 30 seconds total
        
        for attempt in range(max_attempts):
            try:
                # Try to find button with very short timeout
                buy = WebDriverWait(driver, 0.5).until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'a.purchase-button.tickets-available[href$="/buy"]')))
                driver.execute_script("arguments[0].click();", buy)
                logging.info(f"✅ SUCCESS! Clicked buy button (attempt {attempt + 1})")
                button_found = True
                break
            except TimeoutException:
                if attempt % 10 == 0:  # Log every 10th attempt to avoid spam
                    logging.info(f"🔄 Hunting for button... attempt {attempt + 1}/60")
                
                # Aggressive refresh every 2 seconds to catch dynamic content
                if attempt > 0 and attempt % 4 == 0:  # Every 2 seconds (4 x 0.5s)
                    driver.refresh()
                    time.sleep(0.2)  # Brief pause after refresh
                else:
                    time.sleep(0.3)  # Quick retry without refresh
        
        if not button_found:
            logging.warning("❌ Button hunt failed - trying fallback navigation")
            buy_url = url.rstrip("/") + "/buy"
            driver.get(buy_url)
            logging.info(f"📍 Navigated directly to: {buy_url}")

        # 2) Wait for the modal form with aggressive retry
        form = None
        for form_attempt in range(10):  # Try 10 times
            try:
                form = WebDriverWait(driver, 2).until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.modal.current form.custom-form"))
                )
                logging.info("✅ Found purchase form modal")
                break
            except TimeoutException:
                logging.info(f"🔄 Waiting for modal... attempt {form_attempt + 1}/10")
                time.sleep(0.5)
        
        if not form:
            raise Exception("Could not find purchase form modal after 10 attempts")

        # 3) Select tickets: 4 Medlem + 9 Ikke-medlem (works for any event) - AGGRESSIVE
        # First select 4 for Medlem with retry and fallback quantities
        for medlem_attempt in range(3):
            try:
                medlem_select = form.find_element(
                    By.XPATH,
                    './/tr[contains(@class,"price-group-row")][.//td[1][contains(normalize-space(.),"Medlem")]]'
                    '//select[contains(@id,"price_") and contains(@id,"_count")]'
                )
                # Try quantities from 4 down to 1
                selected = False
                for qty in range(MEDLEM_QTY, 0, -1):  # Try 4, 3, 2, 1
                    try:
                        Select(medlem_select).select_by_value(str(qty))
                        logging.info(f"✅ Selected {qty} tickets for Medlem")
                        selected = True
                        break
                    except:
                        continue
                if selected:
                    break
            except Exception as e:
                if medlem_attempt == 2:
                    logging.warning(f"❌ Could not select Medlem tickets after 3 attempts: {e}")
                else:
                    time.sleep(0.5)
        
        # Then select 9 for Ikke-medlem with retry and fallback quantities
        for ikke_medlem_attempt in range(3):
            try:
                ikke_medlem_select = form.find_element(
                    By.XPATH,
                    './/tr[contains(@class,"price-group-row")][.//td[1][contains(normalize-space(.),"Ikke-medlem")]]'
                    '//select[contains(@id,"price_") and contains(@id,"_count")]'
                )
                # Try quantities from 9 down to 1
                selected = False
                for qty in range(IKKE_MEDLEM_QTY, 0, -1):  # Try 9, 8, 7, 6, 5, 4, 3, 2, 1
                    try:
                        Select(ikke_medlem_select).select_by_value(str(qty))
                        logging.info(f"✅ Selected {qty} tickets for Ikke-medlem")
                        selected = True
                        break
                    except:
                        continue
                if selected:
                    break
            except Exception as e:
                if ikke_medlem_attempt == 2:
                    logging.warning(f"❌ Could not select Ikke-medlem tickets after 3 attempts: {e}")
                else:
                    time.sleep(0.5)

        # 4) Fill email aggressively
        for email_attempt in range(3):
            try:
                email_input = WebDriverWait(driver, 3).until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'input#email[name="email"]')
                ))
                email_input.clear()
                email_input.send_keys(EMAIL)
                logging.info("✅ Filled email address")
                break
            except Exception as e:
                if email_attempt == 2:
                    logging.warning(f"❌ Could not fill email after 3 attempts: {e}")
                else:
                    time.sleep(0.5)

        # 5) AGGRESSIVE wait for "Til betaling" with multiple strategies
        def submit_enabled(_):
            try:
                btn = form.find_element(By.CSS_SELECTOR, 'div.payment-submit input[type="submit"][name="commit"]')
                return btn if btn.is_enabled() and btn.get_attribute("disabled") is None else False
            except:
                return False

        submit_btn = None
        for submit_attempt in range(20):  # Try for 20 attempts (about 20 seconds)
            try:
                submit_btn = WebDriverWait(driver, 1).until(submit_enabled)
                break
            except TimeoutException:
                if submit_attempt % 5 == 0:
                    logging.info(f"🔄 Waiting for 'Til betaling' to enable... attempt {submit_attempt + 1}/20")
                time.sleep(1)
        
        if submit_btn:
            # Extra safety - try clicking multiple times if needed
            for click_attempt in range(3):
                try:
                    submit_btn.click()
                    logging.info("✅ SUCCESS! Clicked 'Til betaling' button")
                    break
                except Exception as e:
                    if click_attempt == 2:
                        logging.warning(f"❌ Could not click 'Til betaling' after 3 attempts: {e}")
                    else:
                        time.sleep(0.5)
        
        logging.info("Automation completed - proceeding to payment page")
        logging.info("Complete the bank login and payment manually from here")
            
    except Exception as e:
        logging.error(f"Error during automation: {e}")
        logging.info("You may need to complete the process manually")
        

if __name__ == "__main__":
    # FOR ACTUAL EVENT - 5 seconds before 14:00
    open_event_when_live(
        url=DROP_URL,
        onsale_iso=DROP_TIME,  # 2 seconds before 14:00
        chrome_profile_dir=None  # No profile needed - use fresh browser
    )