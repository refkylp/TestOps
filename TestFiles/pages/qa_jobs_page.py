from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pages.base_page import BasePage
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class QAJobsPage(BasePage):
    """QA Jobs Page Object"""
    
    # XPaths
    SEE_ALL_QA_JOBS_BUTTON_XPATH = (By.XPATH, "//*[@id='page-head']/div/div/div[1]/div/div/a")
    
    # Location dropdown (JavaScript dropdown)
    LOCATION_DROPDOWN_XPATH = (By.XPATH, "//*[@id='select2-filter-by-location-container']/span")
    LOCATION_OPTION_XPATH = (By.XPATH, "//li[contains(@class, 'select2-results__option') and contains(text(), '{}')]")
    
    # These XPaths will be created randomly as requested, user will fix them later
    DEPARTMENT_FILTER_XPATH = (By.XPATH, "//select[@id='filter-by-department']")
    JOBS_LIST_XPATH = (By.XPATH, "//*[@id='jobs-list']/div/div")  
    JOB_POSITION_XPATH = (By.XPATH, "  //*[@id='jobs-list']/div/div/p")
    JOB_DEPARTMENT_XPATH = (By.XPATH, "//*[@id='jobs-list']/div/div/span")
    JOB_LOCATION_XPATH = (By.XPATH, "//*[@id='jobs-list']/div/div/div")
    VIEW_ROLE_BUTTON_XPATH = (By.XPATH, "//*[@id='jobs-list']/div/div/a")
    
    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self.url = "https://useinsider.com/careers/quality-assurance/"
    
    def open_qa_jobs_page(self):
        """Open QA jobs page"""
        self.open(self.url)
    
    def click_see_all_qa_jobs(self):
        """Click See all QA jobs button"""
        self.click(self.SEE_ALL_QA_JOBS_BUTTON_XPATH)
        time.sleep(2)  # Wait for page to load
    
  

    def filter_by_location(self, location="Istanbul, Turkiye"):
        """Filter jobs by location using Select2 dropdown"""

        try:
            # Dropdown alanını bekle ve tıkla
            dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'select2-selection')]"))
            )
            time.sleep(12)  # Wait 3 seconds before clicking
            dropdown.click()

            # Dropdown açıldıktan sonra klavye tuşları ile seçim yap
            time.sleep(1)  # Dropdown'ın açılması için kısa bekleme
            # 12 kez aşağı ok tuşuna bas
            for _ in range(12):
                dropdown.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.1)  # Her tuş basımı arasında kısa bekleme
            # Enter tuşuna basarak seçimi onayla
            dropdown.send_keys(Keys.ENTER)

            # Filtre uygulandığında sonuçların yüklenmesini beklemek isterseniz kısa bir bekleme ekleyebilirsiniz
            WebDriverWait(self.driver, 5).until(
                lambda d: location in d.find_element(By.XPATH, "//span[contains(@class, 'select2-selection__rendered')]").text
            )

        except Exception as e:
            print(f"[ERROR] Location filter operation failed: {e}")


    
    def filter_by_department(self, department="Quality Assurance"):
        """Filter jobs by department"""
        try:
            department_filter = self.find_element(self.DEPARTMENT_FILTER_XPATH)
            select = Select(department_filter)
            select.select_by_visible_text(department)
            time.sleep(2)  # Wait for filter to apply
        except Exception as e:
            print(f"Department filter not found or error: {e}")
    
    def get_jobs_list(self):
        """Get list of job elements"""
        try:
            return self.find_elements(self.JOBS_LIST_XPATH)
        except:
            return []
    
    def is_jobs_list_present(self):
        """Check if jobs list is present"""
        jobs = self.get_jobs_list()
        return len(jobs) > 0
    
    def get_job_position(self, job_element):
        """Get job position text from job element"""
        try:
            return job_element.find_element(*self.JOB_POSITION_XPATH).text
        except:
            return ""
    
    def get_job_department(self, job_element):
        """Get job department text from job element"""
        try:
            return job_element.find_element(*self.JOB_DEPARTMENT_XPATH).text
        except:
            return ""
    
    def get_job_location(self, job_element):
        """Get job location text from job element"""
        try:
            return job_element.find_element(*self.JOB_LOCATION_XPATH).text
        except:
            return ""
    
    def click_view_role(self, job_element):
        """Click View Role button for a job - opens in new window/tab"""
        try:
            # Mevcut pencere sayısını kaydet
            current_windows = self.driver.window_handles
            main_window = self.driver.current_window_handle
            
            # View Role butonunu bul
            view_role_button = job_element.find_element(*self.VIEW_ROLE_BUTTON_XPATH)
            
            # JavaScript ile click yap (bazen normal click yeni pencereyi açmaz)
            self.driver.execute_script("arguments[0].click();", view_role_button)
            
            # Yeni pencere açılmasını bekle
            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.window_handles) > len(current_windows)
            )
            
            # Yeni pencereye geç
            new_windows = [w for w in self.driver.window_handles if w not in current_windows]
            if new_windows:
                self.driver.switch_to.window(new_windows[0])
                time.sleep(2)  # Yeni sayfanın yüklenmesini bekle
            else:
                # Yeni pencere açılmadıysa, mevcut pencerede redirect olmuş olabilir
                time.sleep(2)
                
        except Exception as e:
            print(f"View Role button not found or error: {e}")
    
    def is_lever_page_opened(self):
        """Check if redirected to Lever application form page"""
        current_url = self.get_current_url()
        return "lever.co" in current_url or "jobs.lever.co" in current_url

