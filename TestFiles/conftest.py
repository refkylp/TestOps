import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def find_chromedriver_executable(base_path):
    """Find the actual chromedriver executable in the directory structure"""
    # Check if base_path itself is the executable (and it's actually chromedriver, not THIRD_PARTY_NOTICES)
    if os.path.isfile(base_path) and "THIRD_PARTY_NOTICES" not in base_path:
        # Make it executable if it's chromedriver
        if "chromedriver" in base_path.lower() and not base_path.endswith(".chromedriver"):
            os.chmod(base_path, 0o755)
            return base_path
    
    # Search in the directory
    if os.path.isdir(base_path):
        for root, dirs, files in os.walk(base_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Look for chromedriver (not THIRD_PARTY_NOTICES.chromedriver)
                if file == "chromedriver" and os.path.isfile(file_path) and "THIRD_PARTY_NOTICES" not in file_path:
                    os.chmod(file_path, 0o755)  # Make executable
                    return file_path
    else:
        # If base_path is a file but not executable, search in parent directory
        parent_dir = os.path.dirname(base_path)
        if os.path.isdir(parent_dir):
            for root, dirs, files in os.walk(parent_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file == "chromedriver" and os.path.isfile(file_path) and "THIRD_PARTY_NOTICES" not in file_path:
                        os.chmod(file_path, 0o755)  # Make executable
                        return file_path
    return None


@pytest.fixture(scope="function")
def driver():
    """Setup Chrome WebDriver - supports both local and remote (Kubernetes) execution"""
    chrome_options = Options()

    # Kubernetes ortamında mı çalışıyoruz?
    chrome_node_service = os.getenv('CHROME_NODE_SERVICE')

    # Headless mod için gerekli ayarlar
    if chrome_node_service:
        # Kubernetes/Container ortamı - Headless mod
        chrome_options.add_argument("--headless=new")  # Yeni headless mod (Chrome 109+)
        chrome_options.add_argument("--no-sandbox")  # Docker container için gerekli
        chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm boyut sorunlarını önler
        chrome_options.add_argument("--disable-gpu")  # Headless'te GPU'ya gerek yok
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--window-size=1920,1080")  # Headless için window size
        chrome_options.add_argument("--disable-setuid-sandbox")  # Container güvenlik
    else:
        # Lokal ortam - GUI ile (isterseniz lokal de headless yapabilirsiniz)
        chrome_options.add_argument("--start-maximized")

    # Ortak ayarlar (hem lokal hem remote için)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    if chrome_node_service:
        # Kubernetes ortamında - Remote WebDriver kullan
        print(f"Connecting to remote Chrome Node at: {chrome_node_service}/wd/hub")
        driver = webdriver.Remote(
            command_executor=f"{chrome_node_service}/wd/hub",
            options=chrome_options
        )
    else:
        # Lokal ortamda - Local WebDriver kullan
        print("Running tests locally with ChromeDriver")
        # Get ChromeDriver path from webdriver-manager
        driver_path = ChromeDriverManager().install()

        # Find the actual executable
        chromedriver_executable = find_chromedriver_executable(driver_path)

        if chromedriver_executable:
            service = Service(chromedriver_executable)
        else:
            # Fallback: let Selenium handle it
            service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)

    yield driver

    driver.quit()


@pytest.fixture
def wait(driver):
    """WebDriverWait fixture"""
    return WebDriverWait(driver, 10)

