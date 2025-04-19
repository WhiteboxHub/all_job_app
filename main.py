# import os
# import sys
# import logging
# import json
# import yaml
# import csv
# import time
# import random
# import datetime
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait, Select
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import (
#     NoSuchElementException, TimeoutException,
#     ElementNotInteractableException, StaleElementReferenceException
# )
# from webdriver_manager.chrome import ChromeDriverManager
# import undetected_chromedriver as uc

# # Global variables
# BASE_URLS = {
#     "greenhouse": "https://boards.greenhouse.io",
#     "lever": "https://jobs.lever.co",
#     "jobvite": "https://jobs.jobvite.com"
# }

# # Logging setup
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# def select_application():
#     """Display a menu to select the application."""
#     print("Select the application to run:")
#     print("1. Greenhouse")
#     print("2. Lever")
#     print("3. Jobvite")
#     choice = input("Enter your choice (1/2/3): ")

#     if choice == "1":
#         return "greenhouse"
#     elif choice == "2":
#         return "lever"
#     elif choice == "3":
#         return "jobvite"
#     else:
#         print("Invalid choice. Exiting.")
#         sys.exit(1)

# def select_user_credentials():
#     """Display a menu to select the user credentials."""
#     credential_files = [f for f in os.listdir("credentials") if f.endswith(".yaml")]
#     if not credential_files:
#         print("No credentials found in the 'credentials' directory.")
#         sys.exit(1)

#     print("Available user credentials:")
#     for idx, file in enumerate(credential_files, start=1):
#         print(f"{idx}. {file}")

#     choice = int(input("Select a user credential by number: "))
#     if 1 <= choice <= len(credential_files):
#         return credential_files[choice - 1]
#     else:
#         print("Invalid choice. Exiting.")
#         sys.exit(1)

# def load_config_files(application):
#     """Load the configuration files for the selected application."""
#     answers_file = f"config/{application}_answers.csv"
#     locators_file = f"config/{application}_locators.json"

#     if not os.path.exists(answers_file):
#         print(f"Error: {answers_file} not found.")
#         sys.exit(1)

#     if not os.path.exists(locators_file):
#         print(f"Error: {locators_file} not found.")
#         sys.exit(1)

#     return answers_file, locators_file

# def load_resume_file(application, user):
#     """Load the resume file for the selected application and user."""
#     if application == "jobvite":
#         resume_file = f"resume/{user}.txt"
#     else:
#         resume_file = f"resume/{user}.pdf"

#     if not os.path.exists(resume_file):
#         print(f"Error: {resume_file} not found.")
#         sys.exit(1)

#     return resume_file

# def load_credentials(file_path):
#     """Load the credentials from the selected YAML file."""
#     with open(file_path, "r") as file:
#         return yaml.safe_load(file)

# def load_answers(file_path):
#     """Load the answers from the answers.csv file."""
#     qa_pairs = {}
#     with open(file_path, "r", encoding="utf-8") as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             question = row["question"].strip()
#             answer = row["answer"].strip()
#             qa_pairs[question] = answer
#     return qa_pairs

# def load_locators(file_path):
#     """Load the locators from the locators.json file."""
#     with open(file_path, "r", encoding="utf-8") as file:
#         return json.load(file)

# def run_greenhouse_automation(answers_file, locators_file, resume_file, credentials_file):
#     """Run the Greenhouse automation."""
#     print("Running Greenhouse automation...")

#     # Load answers, locators, and credentials
#     qa_pairs = load_answers(answers_file)
#     locators = load_locators(locators_file)
#     credentials = load_credentials(credentials_file)

#     # Set up the WebDriver
#     options = webdriver.ChromeOptions()
#     options.add_argument("--start-maximized")
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=options)
#     wait = WebDriverWait(driver, 20)

#     # Example: Open a job URL and fill the form
#     job_url = "https://boards.greenhouse.io/example/jobs/12345"
#     driver.get(job_url)

#     # Add your Greenhouse-specific logic here
#     print(f"Filling form for Greenhouse using {qa_pairs}, {locators}, and {credentials}")

#     # Close the driver
#     driver.quit()

# def run_lever_automation(answers_file, locators_file, resume_file, credentials_file):
#     """Run the Lever automation."""
#     print("Running Lever automation...")

#     # Load answers, locators, and credentials
#     qa_pairs = load_answers(answers_file)
#     locators = load_locators(locators_file)
#     credentials = load_credentials(credentials_file)

#     # Set up the WebDriver
#     options = uc.ChromeOptions()
#     options.add_argument("--start-maximized")
#     service = Service(ChromeDriverManager().install())
#     driver = uc.Chrome(options=options, service=service)
#     wait = WebDriverWait(driver, 20)

#     # Example: Open a job URL and fill the form
#     job_url = "https://jobs.lever.co/example/jobs/12345"
#     driver.get(job_url)

#     # Add your Lever-specific logic here
#     print(f"Filling form for Lever using {qa_pairs}, {locators}, and {credentials}")

#     # Close the driver
#     driver.quit()

# def run_jobvite_automation(answers_file, locators_file, resume_file, credentials_file):
#     """Run the Jobvite automation."""
#     print("Running Jobvite automation...")

#     # Load answers, locators, and credentials
#     qa_pairs = load_answers(answers_file)
#     locators = load_locators(locators_file)
#     credentials = load_credentials(credentials_file)

#     # Set up the WebDriver
#     options = webdriver.ChromeOptions()
#     options.add_argument("--start-maximized")
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=options)
#     wait = WebDriverWait(driver, 20)

#     # Example: Open a job URL and fill the form
#     job_url = "https://jobs.jobvite.com/example/job/12345"
#     driver.get(job_url)

#     # Add your Jobvite-specific logic here
#     print(f"Filling form for Jobvite using {qa_pairs}, {locators}, and {credentials}")

#     # Close the driver
#     driver.quit()

# def main():
#     # Step 1: Select the application
#     application = select_application()

#     # Step 2: Select the user credentials
#     user_credentials_file = select_user_credentials()
#     user = os.path.splitext(user_credentials_file)[0]

#     # Step 3: Load the configuration files
#     answers_file, locators_file = load_config_files(application)

#     # Step 4: Load the resume file
#     resume_file = load_resume_file(application, user)

#     # Step 5: Load the credentials
#     credentials = load_credentials(f"credentials/{user_credentials_file}")

#     # Step 6: Run the selected automation
#     if application == "greenhouse":
#         run_greenhouse_automation(answers_file, locators_file, resume_file, f"credentials/{user_credentials_file}")
#     elif application == "lever":
#         run_lever_automation(answers_file, locators_file, resume_file, f"credentials/{user_credentials_file}")
#     elif application == "jobvite":
#         run_jobvite_automation(answers_file, locators_file, resume_file, f"credentials/{user_credentials_file}")
#     else:
#         print("Invalid application selected.")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()




import os
import sys
import logging
import json
import yaml
import csv
import time
import random
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException,
    ElementNotInteractableException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

# Global variables
BASE_URLS = {
    "greenhouse": "https://boards.greenhouse.io",
    "lever": "https://jobs.lever.co",
    "jobvite": "https://jobs.jobvite.com"
}

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

os.makedirs("results", exist_ok=True)

results_filename = "logs/application_results.csv"

def select_application():
    """Display a menu to select the application."""
    print("Select the application to run:")
    print("1. Greenhouse")
    print("2. Lever")
    print("3. Jobvite")
    choice = input("Enter your choice (1/2/3): ")

    if choice == "1":
        return "greenhouse"
    elif choice == "2":
        return "lever"
    elif choice == "3":
        return "jobvite"
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

def select_user_credentials():
    """Display a menu to select the user credentials."""
    credential_files = [f for f in os.listdir("credentials") if f.endswith(".yaml")]
    if not credential_files:
        print("No credentials found in the 'credentials' directory.")
        sys.exit(1)

    print("Available user credentials:")
    for idx, file in enumerate(credential_files, start=1):
        print(f"{idx}. {file}")

    choice = int(input("Select a user credential by number: "))
    if 1 <= choice <= len(credential_files):
        return credential_files[choice - 1]
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

def load_config_files(application):
    """Load the configuration files for the selected application."""
    answers_file = f"config/{application}_answers.csv"
    locators_file = f"locators/{application}_locators.json"

    if not os.path.exists(answers_file):
        print(f"Error: {answers_file} not found.")
        sys.exit(1)

    if not os.path.exists(locators_file):
        print(f"Error: {locators_file} not found.")
        sys.exit(1)

    return answers_file, locators_file

def load_resume_file(application, user):
    """Load the resume file for the selected application and user."""
    if application == "jobvite":
        resume_file = f"resume/{user}.txt"
    else:
        resume_file = f"resume/{user}.pdf"

    if not os.path.exists(resume_file):
        print(f"Error: {resume_file} not found.")
        sys.exit(1)

    return resume_file

def load_credentials(file_path):
    """Load the credentials from the selected YAML file."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

def load_answers(file_path):
    """Load the answers from the answers.csv file."""
    qa_pairs = {}
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            question = row["question"].strip()
            answer = row["answer"].strip()
            qa_pairs[question] = answer
    return qa_pairs

def load_locators(file_path):
    """Load the locators from the locators.json file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def run_greenhouse_automation(answers_file, locators_file, resume_file, credentials_file):
    """Run the Greenhouse automation."""
    print("Running Greenhouse automation...")

    # Load answers, locators, and credentials
    qa_pairs = load_answers(answers_file)
    locators = load_locators(locators_file)
    credentials = load_credentials(credentials_file)

    # Set up the WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)

    # Load job URLs
    job_urls = load_job_urls()

    for job_url in job_urls:
        driver.get(job_url)
        apply_greenhouse(driver, job_url, qa_pairs, locators, credentials)

    # Close the driver
    driver.quit()

def list_users(credentials_dir="credentials"):
    yaml_files = glob.glob(os.path.join(credentials_dir, "*.yaml"))
    users = [os.path.splitext(os.path.basename(file))[0] for file in yaml_files]
    return users

def load_user_credentials(username, credentials_dir="credentials"):
    credentials_file = os.path.join(credentials_dir, f"{username}.yaml")
    return load_credentials(credentials_file)

def load_user_resume(username, resume_dir="resume"):
    resume_file = os.path.join(resume_dir, f"{username}.pdf")
    if not os.path.exists(resume_file):
        print(f"Error: Resume file '{resume_file}' not found for user '{username}'.")
        return None
    return os.path.abspath(resume_file)

def load_job_urls(filename="jobs/linkedin_jobs.csv"):
    job_urls = []
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' was not found.")
        return []
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            platform = row["platform"].strip().lower()
            company = row["company"].strip().replace(" ", "").lower()
            job_id = row["job_id"].strip()
            platform_link = row["platform_link"].strip()
            if platform != "greenhouse":
                continue
            job_url = None
            if company and job_id:
                job_url = f"https://boards.greenhouse.io/{company}/jobs/{job_id}"
            elif platform_link:
                job_url = platform_link
            if job_url:
                job_urls.append(job_url)
            else:
                print(f"Skipping job with missing data: {row}")
    return job_urls

def normalize_text(text):
    return text.strip().lower().replace("*", "").replace(".", "").replace(" ", "")

def apply_greenhouse(driver, url, qa_pairs, locators, credentials):
    print(f"\n🔹 Applying to: {url}")
    driver.get(url)
    random_sleep()

    try:
        apply_button_selectors = locators.get("apply_buttons", [])
        apply_button_clicked = False
        for selector in apply_button_selectors:
            try:
                apply_button = driver.find_element(By.XPATH, selector)
                driver.execute_script("arguments[0].scrollIntoView();", apply_button)
                apply_button.click()
                print(f"'Apply' button clicked using selector: {selector}")
                apply_button_clicked = True
                break
            except (NoSuchElementException, ElementNotInteractableException):
                continue
        if not apply_button_clicked:
            print("No 'Apply' button found. Proceeding with form filling.")
        random_sleep()

        fields = locators.get("fields", {})
        for key, field_id in fields.items():
            try:
                field = driver.find_element(By.ID, field_id)
                field.clear()
                field.send_keys(credentials[key])
                print(f"{key} filled.")
            except NoSuchElementException:
                print(f"{key} field not found. It might be optional.")

        random_sleep()

        try:
            location_input = driver.find_element(By.ID, locators.get("location_input", ""))
            location_input.clear()
            location_input.send_keys(credentials["location"])
            time.sleep(2)
            location_input.send_keys(Keys.ARROW_DOWN)
            location_input.send_keys(Keys.RETURN)
            print(f"Location set to {credentials['location']} (dropdown selected)")
        except NoSuchElementException:
            print("Location input field not found. Skipping.")

        random_sleep()

        try:
            resume_input = driver.find_element(By.CSS_SELECTOR, locators.get("resume_input", ""))
            driver.execute_script("arguments[0].scrollIntoView();", resume_input)
            # resume_input.send_keys(credentials["resume"])
            absolute_resume_path = os.path.abspath(credentials["resume"])
            resume_input.send_keys(absolute_resume_path)
            print("Resume uploaded.")
        except NoSuchElementException:
            print("Resume upload field not found. Skipping.")

        random_sleep()

        text_areas = driver.find_elements(By.CSS_SELECTOR, locators.get("textareas", "textarea"))
        for text_area in text_areas:
            try:
                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{text_area.get_attribute('id')}']")
                question_text = label.text.strip()
                normalized_question = normalize_text(question_text)
                if normalized_question in qa_pairs:
                    print(f"Filling text area: {question_text}")
                    text_area.send_keys(qa_pairs[normalized_question])
                else:
                    print(f"No answer found for question: {question_text}")
            except NoSuchElementException:
                continue

        input_fields = driver.find_elements(By.CSS_SELECTOR, locators.get("input_fields", ""))
        for field in input_fields:
            try:
                aria_label = field.get_attribute("aria-label")
                if not aria_label:
                    continue
                normalized_question = normalize_text(aria_label)
                if normalized_question in qa_pairs:
                    print(f"Filling input field: {aria_label}")
                    field.clear()
                    field.send_keys(qa_pairs[normalized_question])
                else:
                    print(f"No answer found for input field: {aria_label}")
            except Exception as e:
                print(f"Error filling input field: {e}")

        submit_button_selectors = locators.get("submit_buttons", [])
        wait_time = 0
        while True:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                submit_button_clicked = False
                for selector in submit_button_selectors:
                    try:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                        driver.execute_script("arguments[0].scrollIntoView();", submit_button)
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        submit_button.click()
                        print(f"'Submit' button clicked using selector: {selector}")
                        submit_button_clicked = True
                        break
                    except (NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException):
                        continue
                if not submit_button_clicked:
                    print("No 'Submit' button found.")
                time.sleep(8)
                error_elements = driver.find_elements(By.CSS_SELECTOR, locators.get("error_messages", ""))
                if not error_elements:
                    print("All required fields filled. Proceeding with submission.")
                    break
                if wait_time == 0:
                    print("\nSome required fields are missing! Please fill them manually.")
                random_sleep(15, 30)
                wait_time += 20
                if wait_time >= 60:
                    print(f"Waiting... {wait_time} seconds elapsed.")
            except Exception as e:
                print(f"Error checking required fields: {e}")

        try:
            WebDriverWait(driver, 10).until(EC.url_changes(driver.current_url))
            print("Application submitted successfully.")
            log_result_to_csv(results_filename, url, "Success")
        except TimeoutException:
            try:
                confirmation_xpath = locators.get("confirmation_xpath", "")
                confirmation_message = driver.find_element(By.XPATH, confirmation_xpath)
                if confirmation_message:
                    print("Application submitted (confirmation message found).")
                    log_result_to_csv(results_filename, url, "Success")
            except NoSuchElementException:
                print("Submission failed.")
                log_result_to_csv(results_filename, url, "Failed")

    except Exception as e:
        print(f"Error while submitting: {e}")
        log_result_to_csv(results_filename, url, "Failed")

def random_sleep(min_time=2, max_time=8):
    sleep_time = random.uniform(min_time, max_time)
    print(f"Sleeping for {round(sleep_time, 2)} seconds")
    time.sleep(sleep_time)

def log_result_to_csv(filename, url, status):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, mode='a', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([url, status, timestamp])

def initialize_csv(filename):
    with open(filename, mode='w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Status", "Timestamp"])

def run_lever_automation(answers_file, locators_file, resume_file, credentials_file):
    """Run the Lever automation."""
    print("Running Lever automation...")

    # Load answers, locators, and credentials
    qa_pairs = load_answers(answers_file)
    locators = load_locators(locators_file)
    credentials = load_credentials(credentials_file)

    # Set up the WebDriver
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = uc.Chrome(options=options, service=service)
    wait = WebDriverWait(driver, 20)

    # Load job URLs
    job_urls = load_job_urls(filename="jobs/linkedin_jobs.csv", platform="lever")

    for job_url in job_urls:
        driver.get(job_url)
        apply_lever(driver, job_url, qa_pairs, locators, credentials)

    # Close the driver
    driver.quit()

def apply_lever(driver, url, qa_pairs, locators, credentials):
    print(f"\n🔹 Applying to: {url}")
    driver.get(url)
    random_sleep()

    try:
        apply_button_selectors = locators.get("apply_buttons", [])
        apply_button_clicked = False
        for selector in apply_button_selectors:
            try:
                apply_button = driver.find_element(By.XPATH, selector)
                driver.execute_script("arguments[0].scrollIntoView();", apply_button)
                apply_button.click()
                print(f"'Apply' button clicked using selector: {selector}")
                apply_button_clicked = True
                break
            except (NoSuchElementException, ElementNotInteractableException):
                continue
        if not apply_button_clicked:
            print("No 'Apply' button found. Proceeding with form filling.")
        random_sleep()

        fields = locators.get("fields", {})
        for key, field_id in fields.items():
            try:
                field = driver.find_element(By.ID, field_id)
                field.clear()
                field.send_keys(credentials[key])
                print(f"{key} filled.")
            except NoSuchElementException:
                print(f"{key} field not found. It might be optional.")

        random_sleep()

        try:
            location_input = driver.find_element(By.ID, locators.get("location_input", ""))
            location_input.clear()
            location_input.send_keys(credentials["location"])
            time.sleep(2)
            location_input.send_keys(Keys.ARROW_DOWN)
            location_input.send_keys(Keys.RETURN)
            print(f"Location set to {credentials['location']} (dropdown selected)")
        except NoSuchElementException:
            print("Location input field not found. Skipping.")

        random_sleep()

        try:
            resume_input = driver.find_element(By.CSS_SELECTOR, locators.get("resume_input", ""))
            driver.execute_script("arguments[0].scrollIntoView();", resume_input)
            # resume_input.send_keys(credentials["resume"])
            absolute_resume_path = os.path.abspath(credentials["resume"])
            resume_input.send_keys(absolute_resume_path)
            print("Resume uploaded.")
        except NoSuchElementException:
            print("Resume upload field not found. Skipping.")

        random_sleep()

        text_areas = driver.find_elements(By.CSS_SELECTOR, locators.get("textareas", "textarea"))
        for text_area in text_areas:
            try:
                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{text_area.get_attribute('id')}']")
                question_text = label.text.strip()
                normalized_question = normalize_text(question_text)
                if normalized_question in qa_pairs:
                    print(f"Filling text area: {question_text}")
                    text_area.send_keys(qa_pairs[normalized_question])
                else:
                    print(f"No answer found for question: {question_text}")
            except NoSuchElementException:
                continue

        input_fields = driver.find_elements(By.CSS_SELECTOR, locators.get("input_fields", ""))
        for field in input_fields:
            try:
                aria_label = field.get_attribute("aria-label")
                if not aria_label:
                    continue
                normalized_question = normalize_text(aria_label)
                if normalized_question in qa_pairs:
                    print(f"Filling input field: {aria_label}")
                    field.clear()
                    field.send_keys(qa_pairs[normalized_question])
                else:
                    print(f"No answer found for input field: {aria_label}")
            except Exception as e:
                print(f"Error filling input field: {e}")

        submit_button_selectors = locators.get("submit_buttons", [])
        wait_time = 0
        while True:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                submit_button_clicked = False
                for selector in submit_button_selectors:
                    try:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                        driver.execute_script("arguments[0].scrollIntoView();", submit_button)
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        submit_button.click()
                        print(f"'Submit' button clicked using selector: {selector}")
                        submit_button_clicked = True
                        break
                    except (NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException):
                        continue
                if not submit_button_clicked:
                    print("No 'Submit' button found.")
                time.sleep(8)
                error_elements = driver.find_elements(By.CSS_SELECTOR, locators.get("error_messages", ""))
                if not error_elements:
                    print("All required fields filled. Proceeding with submission.")
                    break
                if wait_time == 0:
                    print("\nSome required fields are missing! Please fill them manually.")
                random_sleep(15, 30)
                wait_time += 20
                if wait_time >= 60:
                    print(f"Waiting... {wait_time} seconds elapsed.")
            except Exception as e:
                print(f"Error checking required fields: {e}")

        try:
            WebDriverWait(driver, 10).until(EC.url_changes(driver.current_url))
            print("Application submitted successfully.")
            log_result_to_csv(results_filename, url, "Success")
        except TimeoutException:
            try:
                confirmation_xpath = locators.get("confirmation_xpath", "")
                confirmation_message = driver.find_element(By.XPATH, confirmation_xpath)
                if confirmation_message:
                    print("Application submitted (confirmation message found).")
                    log_result_to_csv(results_filename, url, "Success")
            except NoSuchElementException:
                print("Submission failed.")
                log_result_to_csv(results_filename, url, "Failed")

    except Exception as e:
        print(f"Error while submitting: {e}")
        log_result_to_csv(results_filename, url, "Failed")

def run_jobvite_automation(answers_file, locators_file, resume_file, credentials_file):
    """Run the Jobvite automation."""
    print("Running Jobvite automation...")

    # Load answers, locators, and credentials
    qa_pairs = load_answers(answers_file)
    locators = load_locators(locators_file)
    credentials = load_credentials(credentials_file)

    # Set up the WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)

    # Load job URLs
    job_urls = generate_job_links("jobs/linkedin_jobs.csv")
    print("*********************Job URL************:", job_urls, type(job_urls))

    for job_url in job_urls:
        driver.get(job_url)
        apply_jobvite(driver, job_url, qa_pairs, locators, credentials)

    # Close the driver
    driver.quit()

def generate_job_links(csv_filename):
    job_links = []

    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                company = row.get("company", "").strip()
                job_id = row.get("job_id", "").strip()
                fallback_url = row.get("platform_link", "").strip()
                platform = row.get("platform", "").strip().lower()
                print("******************",fallback_url)
                final_url = None

                if platform == "jobvite":
                    if company and job_id:
                        final_url = f"{BASE_URLS['jobvite']}/{company}/job/{job_id}"
                    elif fallback_url:
                        final_url = fallback_url
                        logging.warning(f"Falling back to platform_link for row: {row}")
                    else:
                        logging.warning(f"Missing data to construct URL and no fallback: {row}")
                        continue

                    job_data = {
                        "company": company,
                        "job_id": job_id,
                        "url": final_url
                    }
                    job_links.append(job_data)
                else:
                    logging.info(f"Skipping non-Jobvite platform: {row}")

        logging.info(f"Loaded {len(job_links)} Jobvite job entries from {csv_filename}")

    except FileNotFoundError:
        logging.error(f"CSV file {csv_filename} not found.")
    except Exception as e:
        logging.exception(f"Unexpected error while reading {csv_filename}: {e}")

    return job_links

def apply_jobvite(driver, job_url, qa_pairs, locators, credentials):
    print(f"\n🔹 Applying to: {job_url}")
    driver.get(job_url)
    random_sleep()

    try:
        apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Apply') or contains(@class, 'apply-button')]")))
        apply_button.click()
        print("Clicked Apply button.")
        time.sleep(5)

        filled_locators = set()

        elements = driver.find_elements(By.XPATH, '//*[@required="required"]')

        for element in elements:
            element_id = element.get_attribute("id")
            element_value = element.get_attribute("value") or element.get_attribute("name")
            autocomplete_attr = element.get_attribute("autocomplete")

            print(f"ID: {element_id}, Value: {element_value}, Autocomplete: {autocomplete_attr}")

            label = None
            for i in range(1, 6):
                label_xpath = f'./ancestor::*[{i}]/label'
                label_element = element.find_elements(By.XPATH, label_xpath)
                if label_element:
                    label = label_element[0].text
                    break

            label_text = label if label else "No label found"

            print(f"ID: {element_id}, Value: {element_value}, Nearest Label: {label_text}")

        select_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Select')]")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_button)
        time.sleep(1)

        try:
            select_button.click()
            print("Clicked Select button for resume upload.")
        except Exception as e:
            logging.warning(f"Click intercepted. Trying JavaScript click instead. Error: {e}")
            driver.execute_script("arguments[0].click();", select_button)

        time.sleep(2)

        upload_resume(driver, credentials["resume"])

        execute_automation(driver, locators, filled_locators)
        handle_uninteracted_required_elements(driver, credentials, filled_locators)
        qa_data = read_csv("config/answers.csv")
        fill_form(driver, qa_data, filled_fields, filled_locators)
        wait_until_all_required_filled(driver)

        next_button = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "button.jv-button.jv-button-primary.jv-button-large"
        )))
        next_button.click()
        print("------Clicked Next button----")
        time.sleep(5)

        execute_automation(driver, locators, filled_locators)
        handle_uninteracted_required_elements(driver, credentials, filled_locators)
        qa_data = read_csv("config/answers.csv")
        fill_form(driver, qa_data, filled_fields, filled_locators)
        wait_until_all_required_filled(driver)

        try:
            next_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, "button.jv-button.jv-button-primary.jv-button-large"
            )))
            next_button.click()
            print("-----Clicked the Next button proceeding to the next page-----")
            time.sleep(5)
            print("---- Clicked the Next button proceeding to the next page-------")

            execute_automation(driver, locators, filled_locators)
            handle_uninteracted_required_elements(driver, credentials, filled_locators)
            qa_data = read_csv("config/answers.csv")
            fill_form(driver, qa_data, filled_fields, filled_locators)
            wait_until_all_required_filled(driver)

        except:
            send_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jv-button-primary') and contains(., 'Send Application')]")))
            driver.execute_script("arguments[0].click();", send_button)
            print("No Next button found, clicked Send Application.")
            # time.sleep(20)

        send_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jv-button-primary') and contains(., 'Send Application')]")))
        driver.execute_script("arguments[0].click();", send_button)
        print("------Clicked 'Send Application' button-------")
        # time.sleep(20)

        try:
            confirmation_message = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "h2.jv-page-message-header"
            )))
            print("---------------------Applied_Successfully----------------------------------------")
            logging.info("Application submitted successfully!")
            log_job_status(job_link, "Successfully Applied")

        except TimeoutException:
            try:
                already_applied_message = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "p.jv-page-error-header"
                )))
                print("---------------------------already_applied----------------------------------------")
                logging.info("-----You have already submitted the application------")
                log_job_status(job_link, "Already Submitted")

            except TimeoutException:
                logging.error("Unable to submit the application and no confirmation message found.")
                log_job_status(job_link, "Submission Failed")

    except TimeoutException:
        logging.error(f"Timeout: Could not find elements for job {job_link}")
        log_job_status(job_link, "Failed")
    except NoSuchElementException as e:
        logging.error(f"Error applying for job: {e}")
        log_job_status(job_link, "Failed")

def upload_resume(driver, resume_path):
    try:
        with open(resume_path, 'r') as file:
            resume_text = file.read()

        paste_resume_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.jv-text-block.jv-text-link.needsclick.ng-binding"))
        )
        paste_resume_button.click()
        logging.info("Selected 'Type or Paste Resume' option.")

        textarea = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#jv-paste-resume-textarea0"))
        )
        textarea.clear()
        textarea.send_keys(resume_text)
        logging.info("Pasted resume text into the textarea.")

        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jv-button.jv-button-primary[ng-disabled='!pastedText']"))
        )
        save_button.click()
        logging.info("Clicked the Save button after pasting the resume.")

    except NoSuchElementException as e:
        logging.error(f"Element not found during resume upload: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main():
    # Step 1: Select the application
    application = select_application()

    # Step 2: Select the user credentials
    user_credentials_file = select_user_credentials()
    user = os.path.splitext(user_credentials_file)[0]

    # Step 3: Load the configuration files
    answers_file, locators_file = load_config_files(application)

    # Step 4: Load the resume file
    resume_file = load_resume_file(application, user)

    # Step 5: Load the credentials
    credentials = load_credentials(f"credentials/{user_credentials_file}")

    # Step 6: Run the selected automation
    if application == "greenhouse":
        run_greenhouse_automation(answers_file, locators_file, resume_file, f"credentials/{user_credentials_file}")
    elif application == "lever":
        run_lever_automation(answers_file, locators_file, resume_file, f"credentials/{user_credentials_file}")
    elif application == "jobvite":
        run_jobvite_automation(answers_file, locators_file, resume_file, f"credentials/{user_credentials_file}")
    else:
        print("Invalid application selected.")
        sys.exit(1)

if __name__ == "__main__":
    main()
