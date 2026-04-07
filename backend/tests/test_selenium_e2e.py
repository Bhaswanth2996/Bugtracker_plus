import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.mark.e2e
def test_frontend_login_page_loads() -> None:
    frontend_url = os.getenv("E2E_FRONTEND_URL")
    if not frontend_url:
        pytest.skip("E2E_FRONTEND_URL not configured for Selenium test run.")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(frontend_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Login') or contains(text(), 'Sign In')]"))
        )
    finally:
        driver.quit()
