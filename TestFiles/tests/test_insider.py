from pages.home_page import HomePage
from pages.careers_page import CareersPage
from pages.qa_jobs_page import QAJobsPage


class TestInsider:
    
    def test_1_home_page_opened(self, driver, wait):
        """Test 1: Visit https://useinsider.com/ and check Insider home page is opened or not"""
        home_page = HomePage(driver, wait)
        home_page.open_home_page()
        
        assert home_page.is_home_page_opened(), "Home page is not opened"
    
    def test_2_careers_page_blocks(self, driver, wait):
        """Test 2: Select Company menu, select Careers and check Career page blocks"""
        home_page = HomePage(driver, wait)
        home_page.open_home_page()
        
        # Hover over Company menu and click Careers
        home_page.hover_company_menu()
        home_page.click_careers()
        
        # Check Careers page blocks
        careers_page = CareersPage(driver, wait)
        
        assert careers_page.is_careers_page_opened(), "Careers page is not opened"
        assert careers_page.is_location_block_present(), "Locations block is not present"
        assert careers_page.is_teams_block_present(), "Teams block is not present"
        assert careers_page.is_life_at_insider_block_present(), "Life at Insider block is not present"
    
    def test_3_qa_jobs_filtering(self, driver, wait):
        """Test 3: Go to QA jobs page, click See all QA jobs, filter by Location and Department"""
        qa_jobs_page = QAJobsPage(driver, wait)
        qa_jobs_page.open_qa_jobs_page()
        
        # Click See all QA jobs button
        qa_jobs_page.click_see_all_qa_jobs()
        
        # Filter by Location - Istanbul, Turkey
        qa_jobs_page.filter_by_location("Istanbul, Turkiye")
        
        # Filter by Department - Quality Assurance
        qa_jobs_page.filter_by_department("Quality Assurance")
        
        # Check presence of jobs list
        assert qa_jobs_page.is_jobs_list_present(), "Jobs list is not present"
    
    def test_4_job_details_verification(self, driver, wait):
        """Test 4: Check that all jobs contain Quality Assurance in Position and Department, Istanbul, Turkiye in Location"""
        qa_jobs_page = QAJobsPage(driver, wait)
        qa_jobs_page.open_qa_jobs_page()
        
        # Click See all QA jobs button
        qa_jobs_page.click_see_all_qa_jobs()
        
        # Filter by Location - Istanbul, Turkiye
        qa_jobs_page.filter_by_location("Istanbul, Turkiye")
        
        # Filter by Department - Quality Assurance
        qa_jobs_page.filter_by_department("Quality Assurance")
        
        # Get jobs list
        jobs = qa_jobs_page.get_jobs_list()
        
        assert len(jobs) > 0, "No jobs found"
        
        # Verify each job
        for job in jobs:
            position = qa_jobs_page.get_job_position(job)
            department = qa_jobs_page.get_job_department(job)
            location = qa_jobs_page.get_job_location(job)
            
            assert "Quality Assurance" in position, f"Position '{position}' does not contain 'Quality Assurance'"
            assert "Quality Assurance" in department, f"Department '{department}' does not contain 'Quality Assurance'"
            assert "Istanbul, Turkiye" in location, f"Location '{location}' does not contain 'Istanbul, Turkiye'"
    
    def test_5_view_role_redirect(self, driver, wait):
        """Test 5: Click View Role button and check redirect to Lever Application form page"""
        qa_jobs_page = QAJobsPage(driver, wait)
        qa_jobs_page.open_qa_jobs_page()
        
        # Click See all QA jobs button
        qa_jobs_page.click_see_all_qa_jobs()
        
        # Filter by Location - Istanbul, Turkiye
        qa_jobs_page.filter_by_location("Istanbul, Turkiye")
        
        # Filter by Department - Quality Assurance
        qa_jobs_page.filter_by_department("Quality Assurance")
        
        # Get jobs list
        jobs = qa_jobs_page.get_jobs_list()
        
        assert len(jobs) > 0, "No jobs found"
        
        # Click View Role button on first job
        qa_jobs_page.click_view_role(jobs[0])
        
        # Check if redirected to Lever page
        assert qa_jobs_page.is_lever_page_opened(), "Not redirected to Lever application form page"

