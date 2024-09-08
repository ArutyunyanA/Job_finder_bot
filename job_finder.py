import time
import logging
import random
from constant import url, user_name, password, user_agents, key_words, letter  # Import constants from a separate module
from selenium import webdriver  # Import selenium webdriver
from selenium.webdriver.common.by import By  # Used for locating elements on the page
from selenium.webdriver.common.keys import Keys  # Used for sending keystrokes
from selenium.webdriver.support import expected_conditions as EC  # Used for waiting conditions
from selenium.webdriver.support.ui import WebDriverWait  # Used for explicit waits
from selenium.webdriver.firefox.options import Options  # Firefox options for headless mode
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException  # Common exceptions

# Define a class for browser automation
class BrowserAutomation:

    # Initialize the class with browser and optional user agent
    def __init__(self, browser, user_agent=None):
        self.browser = browser.lower()
        self.user_agent = user_agent
        self.driver = self._create_driver()  # Create the webdriver instance
        self.logger = self._setup_logger()  # Set up the logger

    # Private method to create a browser driver
    def _create_driver(self):
        if self.browser == 'firefox':
            options = webdriver.FirefoxOptions()  # Firefox options instance
            profile = webdriver.FirefoxProfile()  # Create a new Firefox profile
            profile.set_preference("dom.disable_open_during_load", True)  # Disable pop-ups
            if self.user_agent:
                profile.set_preference("general.useragent.override", self.user_agent)  # Set custom user agent
            options.profile = profile
            driver = webdriver.Firefox(options=options)  # Create the Firefox driver
        else:
            raise ValueError("Unsupported browser. Choose the 'firefox' as main browser")
        return driver

    # Private method to set up the logger
    def _setup_logger(self):
        logger = logging.getLogger(__name__)  # Create logger instance
        handler = logging.StreamHandler()  # Create handler for output stream
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # Log format
        handler.setFormatter(formatter)  # Set formatter for the handler
        logger.addHandler(handler)  # Add handler to logger
        logger.setLevel(logging.INFO)  # Set log level to INFO
        return logger

    # Open the landing page
    def landing_page(self, url):
        try:
            self.driver.get(url)  # Navigate to the URL
            close_cookies = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'fc-button') and .//p[text()='Soglašam']]"))
                )  # Wait for cookie consent button
            time.sleep(random.uniform(0.3, 0.7))  # Random delay to mimic human behavior
            close_cookies.click()  # Click to close cookies popup
            close_popup = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "btnPopupDesktopClose"))
                )  # Wait for the close button of another popup
            time.sleep(random.uniform(0.3, 0.7))  # Random delay
            close_popup.click()  # Close the popup
            # self.login(user_name, password)
        except WebDriverException as error:
            self.logger.error(f"Webdriver Error: {error}")
        except NoSuchElementException as error:
            self.logger.error(f"Element not found: {error}")
        except TimeoutException as error:
            self.logger.error(f"Operation timed out: {error}")
    
    # Login to the website
    def login(self, user_name, password):
        try:
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@class='user-link login']"))
            )  # Wait for login button to be clickable
            login_btn.click()  # Click the login button

            name = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "Email"))
            )  # Wait for email input to be visible

            pswd = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "Password"))
            )  # Wait for password input to be visible
            self.human_type(name, user_name)  # Enter the username
            self.human_type(pswd, password)  # Enter the password

            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )  # Wait for submit button to be clickable
            submit_btn.click()  # Click the submit button
        except NoSuchElementException as error:
            self.logger.error(f"No found element for login: {error}")
        except TimeoutException as error:
            self.logger.error(f"Operation timed out during login: {error}")

    # Search for jobs using specified keywords
    def search_jobs(self, key_words):
        try:
            # Navigate to the "Delovna mesta" section
            link = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'w-nav-link nav-link') and contains(text(), 'Delovna mesta')]"))
            )
            link.click()

            unique_links = set()  # To store unique job links
            current_page = set()

            while True:  # Loop for handling pagination
                self.smooth_scroll()  # Scroll to load more content
                time.sleep(random.uniform(1, 5))  # Random delay
                job_elements = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@href and descendant::h2[@class='title']]"))
                )  # Get all job elements
                # Extract href links and titles from job elements
                jobs = [(job_element.get_attribute('href'), job_element.find_element(By.XPATH, ".//h2[@class='title']").text.strip()) for job_element in job_elements]
                # Filter links by keywords
                filtered_links = [(link, title) for link, title in jobs if any(keyword.lower() in title.lower() for keyword in key_words)]
                page_link = set(link for link, title in filtered_links)  # Add filtered links to the set
                current_page.update(page_link)
                new_link = page_link - unique_links
                unique_links.update(new_link)
                for link in new_link:
                    self.apply_to_job(link)  # Apply to each job link
                try:
                    next_button = WebDriverWait(self.driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'PagedList-skipToNext')]"))
                        )  # Wait for "Next" button
                    next_button.click()  # Click the "Next" button to navigate to the next page
                    time.sleep(random.uniform(2, 4))  # Pause to mimic natural behavior
                except TimeoutException:
                    self.logger.info("No more pages to navigate.")
                    break  # Exit the loop if there are no more pages

        except NoSuchElementException as error:
            self.logger.error(f"No found element for search jobs: {error}")
        except TimeoutException as error:
            self.logger.error(f"Operation timed out during search jobs: {error}")

    # Apply to a specific job link
    def apply_to_job(self, link):
        """Performs application steps for a specific job."""
        try:
            self.driver.get(link)  # Open the job link
            time.sleep(random.uniform(1, 3))  # Random delay

            # Click the button to start the application process
            apply_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'button') and contains(text(), 'Prijavi se na to delovno mesto')]"))
            )
            apply_button.click()
            cover_letter = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "CoverLetter"))
            )
            self.human_type(cover_letter, letter)  # Fill with a sample cover letter
            self.smooth_scroll()

            # Select citizenship
            container = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "CitizenshipId_chosen"))
            )
            citizenship_dropdown = container.find_element(By.XPATH, ".//a[@class='chosen-single']")
            citizenship_dropdown.click()
            citizenship_input = container.find_element(By.XPATH, ".//div[@class='chosen-drop']//input[@type='text' and @autocomplete='off']")
            self.human_type(citizenship_input, "Rusko")  # Enter citizenship
            time.sleep(random.uniform(0.5, 1))
            citizenship_input.send_keys(Keys.ENTER)

            # Click the "Continue" button
            continue_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and @name='ApplyEmail']"))
            )
            continue_button.click()

            # Click the "Confirm and Submit Application" button
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(@class, 'modal-btn mt20 mb40')]"))
            )
            submit_button.click()
            self.driver.back()

        except NoSuchElementException as error:
            self.logger.error(f"Element not found while applying to job: {error}")
        except TimeoutException as error:
            self.logger.error(f"Operation timed out while applying to job: {error}")
        except Exception as error:
            self.logger.error(f"An unexpected error occurred: {error}")


    # Method to scroll smoothly through the page
    def smooth_scroll(self, min_pause_time=0.5, max_pause_time=1.5, scroll_step=300):
        last_height = self.driver.execute_script("return document.body.scrollHeight")  # Get current scroll height
        while True:
            self.driver.execute_script(f"window.scrollBy(0, {scroll_step})")  # Scroll by step amount
            time.sleep(random.uniform(min_pause_time, max_pause_time))  # Random delay to mimic human scrolling
            new_height = self.driver.execute_script("return document.body.scrollHeight")  # Get new scroll height
            if new_height == last_height:
                break  # Stop scrolling if no more new content is loaded
            last_height = new_height
    
    # Method to simulate human typing
    def human_type(self, element, text, delay=0.1):
        for char in text:
            element.send_keys(char)  # Send each character one by one
            time.sleep(delay)  # Delay between characters

# Main execution point
if __name__ == "__main__":
    user_agent = random.choice(user_agents)  # Randomly select a user agent
    bot = BrowserAutomation(browser='firefox', user_agent=user_agent)  # Create a browser automation instance
    try:
        bot.landing_page(url)  # Open the landing page
        bot.login(user_name, password)  # Perform login
        bot.search_jobs(key_words)  # Search for jobs
    except (NoSuchElementException, TimeoutException, WebDriverException) as error:
        bot.logger.error(f"An error occured: {error}")  # Log errors
    finally:
        time.sleep(10)  # Wait before closing
        bot.driver.quit()  # Quit the browser