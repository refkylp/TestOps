from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class HomePage(BasePage):
    """Home Page Object"""
    
    # XPaths
    COMPANY_XPATH = (By.XPATH, "/html/body/nav/div[2]/div/ul[1]/li[6]/a")
    CAREERS_XPATH = (By.XPATH, "//*[@id='navbarNavDropdown']/ul[1]/li[6]/div/div[2]/a[2]")
    
    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self.url = "https://useinsider.com/"
    
    def open_home_page(self):
        """Open Insider home page"""
        self.open(self.url)
    
    def is_home_page_opened(self):
        """Check if home page is opened"""
        return "useinsider.com" in self.get_current_url()
    
    def hover_company_menu(self):
        """Hover over Company menu"""
        from selenium.webdriver.common.action_chains import ActionChains
        company_element = self.find_element(self.COMPANY_XPATH)
        ActionChains(self.driver).move_to_element(company_element).perform()
    
    def click_careers(self):
        """Click Careers link"""
        self.click(self.CAREERS_XPATH)

