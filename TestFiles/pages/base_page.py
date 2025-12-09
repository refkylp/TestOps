from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class BasePage:
    """Base page class with common methods"""
    
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
    
    def open(self, url):
        """Navigate to URL"""
        self.driver.get(url)
    
    def find_element(self, locator, timeout=10):
        """Find element with wait"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
    
    def find_elements(self, locator, timeout=10):
        """Find elements with wait"""
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return self.driver.find_elements(*locator)
    
    def click(self, locator, timeout=10):
        """Click element with wait"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
    
    def is_element_present(self, locator, timeout=10):
        """Check if element is present"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except:
            return False
    
    def get_text(self, locator, timeout=10):
        """Get text from element"""
        element = self.find_element(locator, timeout)
        return element.text
    
    def get_current_url(self):
        """Get current URL"""
        return self.driver.current_url

