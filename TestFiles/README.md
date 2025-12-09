# TestOps - Insider Website Test Automation

This project contains automated tests for the Insider website using pytest and Selenium with Page Object Model (POM) pattern.

## Project Structure

```
TestFiles/
├── pages/
│   ├── __init__.py
│   ├── base_page.py          # Base page class with common methods
│   ├── home_page.py          # Home page object
│   ├── careers_page.py       # Careers page object
│   └── qa_jobs_page.py       # QA Jobs page object
├── tests/
│   ├── __init__.py
│   └── test_insider.py       # Test cases
├── conftest.py               # Pytest fixtures (WebDriver setup)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Setup

1. Install Python 3.7 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest tests/test_insider.py -v
```

Run specific test:
```bash
pytest tests/test_insider.py::TestInsider::test_1_home_page_opened -v
```

Run with HTML report:
```bash
pytest tests/test_insider.py --html=report.html
```

## Test Cases

1. **test_1_home_page_opened**: Verifies that Insider home page opens correctly
2. **test_2_careers_page_blocks**: Verifies Company menu, Careers page, and its blocks (Locations, Teams, Life at Insider)
3. **test_3_qa_jobs_filtering**: Verifies QA jobs page filtering functionality
4. **test_4_job_details_verification**: Verifies that all filtered jobs contain correct Position, Department, and Location
5. **test_5_view_role_redirect**: Verifies that clicking "View Role" redirects to Lever application form page

## Notes

- Chrome WebDriver is automatically managed by webdriver-manager
- Some XPaths in `qa_jobs_page.py` are placeholders and need to be updated based on actual page structure
- Tests include waits and delays to handle dynamic content loading

