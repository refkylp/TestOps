from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class CareersPage(BasePage):
    """Careers Page Object"""
    
    # XPaths
    LOCATION_XPATH = (By.XPATH, "//*[@id='career-our-location']/div/div/div/div[1]/h3")
    TEAMS_XPATH = (By.XPATH, "//*[@id='career-find-our-calling']/div/div/div[1]/h3")
    LIFE_AT_INSIDER_XPATH = (By.XPATH, "/html/body/div[2]/section[4]/div/div/div/div[1]/div/h2")
    
    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self.url = "https://useinsider.com/careers/"
    
    def is_careers_page_opened(self):
        """Check if careers page is opened"""
        return "careers" in self.get_current_url().lower()
    
    def is_location_block_present(self):
        """Check if Locations block is present"""
        return self.is_element_present(self.LOCATION_XPATH)
    
    def is_teams_block_present(self):
        """Check if Teams block is present"""
        return self.is_element_present(self.TEAMS_XPATH)
    
    def is_life_at_insider_block_present(self):
        """Check if Life at Insider block is present"""
        return self.is_element_present(self.LIFE_AT_INSIDER_XPATH)

