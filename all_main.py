import os
import sys
import logging
import json
import yaml
import csv
import time
import random
import datetime
import glob
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

# Configure logging
os.makedirs("logs", exist_ok=True)
os.makedirs("results", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/automation.log"), logging.StreamHandler()],
)

# Global variables
BASE_URLS = {
    "greenhouse": "https://boards.greenhouse.io",
    "lever": "https://jobs.lever.co",
    "jobvite": "https://jobs.jobvite.com",
}

results_filename = "results/application_results.csv"


def initialize_csv(filename):
    """Initialize the CSV file with headers if it doesn't exist."""
    if not os.path.exists(filename):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["URL", "Status", "Timestamp"])
        print(f"Initialized CSV file: {filename}")
    else:
        print(f"CSV file already exists: {filename}")


# Ensure this is called at the start of your script
initialize_csv(results_filename)


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


def load_config_files(application, user_credential_file):
    """Load and validate all configuration files for the application."""
    # Load credentials from the selected user file
    try:
        with open(f"credentials/{user_credential_file}", "r") as stream:
            credentials = yaml.safe_load(stream)
    except FileNotFoundError:
        print(f"Error: Credentials file not found: credentials/{user_credential_file}")
        return None, None, None
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return None, None, None

    # Validate required fields
    required_fields = [
        "full_name",
        "email",
        "phone",
        "linkedin",
        "resume_path",
        "current_company",
        "current_location",
    ]
    for field in required_fields:
        if field not in credentials:
            print(f"Error: Required field '{field}' missing in credentials")
            return None, None, None

    # Clean phone number
    phone = credentials["phone"]
    cleaned_phone = re.sub(r"[^\d+]", "", phone)
    if not re.match(r"^\+?\d{8,15}$", cleaned_phone):
        print(f"Warning: Phone number format may be invalid: {phone}")

    # Handle optional fields
    credentials["github"] = str(credentials.get("github", ""))
    credentials["portfolio"] = str(credentials.get("portfolio", ""))
    credentials["work_status"] = str(credentials.get("work_status", ""))

    # Verify resume file exists
    resume_path = credentials["resume_path"]
    if not os.path.isfile(resume_path):
        print(f"Error: Resume file not found at: {resume_path}")
        return None, None, None
    credentials["resume"] = resume_path

    # Load locators
    try:
        with open(f"locators/{application}_locators.json", "r") as f:
            locators = json.load(f)
    except FileNotFoundError:
        print(f"Error: Locators file not found: locators/{application}_locators.json")
        return None, None, None
    except json.JSONDecodeError:
        print("Error: Invalid JSON in locators file")
        return None, None, None

    # Validate required locator sections
    required_sections = ["APPLY_SELECTORS", "FIELD_SELECTORS", "SUBMIT_SELECTORS"]
    for section in required_sections:
        if section not in locators:
            print(f"Error: Required section '{section}' missing in locators")
            return None, None, None

    # Load answers
    try:
        with open(
            f"config/{application}_answers.csv", mode="r", encoding="utf-8"
        ) as file:
            reader = csv.DictReader(file)
            answers = {}
            for row in reader:
                question = row["Question"].strip().lower()
                answers[question] = row["Answer"].strip()
    except FileNotFoundError:
        print(f"Error: Answers file not found: config/{application}_answers.csv")
        return None, None, None
    except Exception as e:
        print(f"Error loading answers: {e}")
        return None, None, None

    return answers, locators, credentials


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


def run_greenhouse_automation(
    answers_file, locators_file, resume_file, credentials_file
):
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
    job_urls = load_job_urls(platform="greenhouse")

    for job_url in job_urls:
        driver.get(job_url)
        apply_greenhouse(driver, job_url, qa_pairs, locators, credentials)

    # Close the driver
    driver.quit()


def load_job_urls(filename="jobs/linkedin_jobs.csv", platform="greenhouse"):
    """Load job URLs from a CSV file for a specific platform."""
    job_urls = []
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' was not found.")
        return []

    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row_platform = row["platform"].strip().lower()
            company = row["company"].strip().replace(" ", "").lower()
            job_id = row["job_id"].strip()
            platform_link = row["platform_link"].strip()

            if row_platform != platform:
                logging.info(f"Skipping non-{platform} platform: {row}")
                continue

            job_url = None
            if platform == "greenhouse" and company and job_id:
                job_url = f"https://boards.greenhouse.io/{company}/jobs/{job_id}"
            elif platform == "lever" and company and job_id:
                job_url = f"https://jobs.lever.co/{company}/{job_id}"
            elif platform == "jobvite" and company and job_id:
                job_url = f"https://jobs.jobvite.com/{company}/job/{job_id}"
            elif platform_link:
                job_url = platform_link

            if job_url:
                if platform == "jobvite":
                    job_urls.append(
                        {"company": company, "job_id": job_id, "url": job_url}
                    )
                else:
                    job_urls.append(job_url)

    logging.info(f"Loaded {len(job_urls)} {platform} job entries from {filename}")
    return job_urls


def normalize_text(text):
    """Normalize text for comparison."""
    if not text:
        return ""
    return re.sub(r"[^a-zA-Z0-9\s]", "", text).strip().lower()


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
            location_input = driver.find_element(
                By.ID, locators.get("location_input", "")
            )
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
            resume_input = driver.find_element(
                By.CSS_SELECTOR, locators.get("resume_input", "")
            )
            driver.execute_script("arguments[0].scrollIntoView();", resume_input)
            absolute_resume_path = os.path.abspath(credentials["resume"])
            resume_input.send_keys(absolute_resume_path)
            print("Resume uploaded.")
        except NoSuchElementException:
            print("Resume upload field not found. Skipping.")

        random_sleep()

        text_areas = driver.find_elements(
            By.CSS_SELECTOR, locators.get("textareas", "textarea")
        )
        for text_area in text_areas:
            try:
                label = driver.find_element(
                    By.CSS_SELECTOR, f"label[for='{text_area.get_attribute('id')}']"
                )
                question_text = label.text.strip()
                normalized_question = normalize_text(question_text)
                if normalized_question in qa_pairs:
                    print(f"Filling text area: {question_text}")
                    text_area.send_keys(qa_pairs[normalized_question])
                else:
                    print(f"No answer found for question: {question_text}")
            except NoSuchElementException:
                continue

        input_fields = driver.find_elements(
            By.CSS_SELECTOR, locators.get("input_fields", "")
        )
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
                        driver.execute_script(
                            "arguments[0].scrollIntoView();", submit_button
                        )
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        submit_button.click()
                        print(f"'Submit' button clicked using selector: {selector}")
                        submit_button_clicked = True
                        break
                    except (
                        NoSuchElementException,
                        ElementNotInteractableException,
                        StaleElementReferenceException,
                    ):
                        continue
                if not submit_button_clicked:
                    print("No 'Submit' button found.")
                time.sleep(8)
                error_elements = driver.find_elements(
                    By.CSS_SELECTOR, locators.get("error_messages", "")
                )
                if not error_elements:
                    print("All required fields filled. Proceeding with submission.")
                    break
                if wait_time == 0:
                    print(
                        "\nSome required fields are missing! Please fill them manually."
                    )
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
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([url, status, timestamp])


def run_lever_automation(answers_file, locators_file, resume_file, credentials_file):
    """Run the Lever automation."""
    print("Running Lever automation...")

    # Load answers, locators, and credentials
    qa_pairs, locators, credentials = load_config_files(
        "lever", select_user_credentials()
    )

    # Set up the WebDriver
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = uc.Chrome(options=options, service=service)
    wait = WebDriverWait(driver, 20)

    # Load job URLs
    job_urls = load_job_urls(platform="lever")

    for job_url in job_urls:
        driver.get(job_url)
        apply_lever(driver, job_url, qa_pairs, locators, credentials)

    # Close the driver
    driver.quit()


def apply_lever(driver, url, qa_pairs, locators, credentials):
    print(f"\n🔹 Applying to: {url}")
    driver.get(url)
    time.sleep(2)

    try:
        # Try to find and click the Apply button
        apply_button_selectors = locators.get("APPLY_SELECTORS", [])
        apply_button_clicked = False

        for selector in apply_button_selectors:
            try:
                if selector["type"] == "css":
                    apply_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, selector["value"])
                        )
                    )
                elif selector["type"] == "xpath":
                    apply_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector["value"]))
                    )
                else:
                    continue

                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", apply_button
                )
                time.sleep(1)

                try:
                    driver.execute_script("arguments[0].click();", apply_button)
                    apply_button_clicked = True
                    break
                except Exception:
                    try:
                        apply_button.click()
                        apply_button_clicked = True
                        break
                    except Exception:
                        continue

            except Exception:
                continue

        if not apply_button_clicked:
            print("No 'Apply' button found. Proceeding with form filling.")

        # Wait for form to load
        print("Waiting for application form to load...")
        time.sleep(5)

        # Upload resume first
        resume_selectors = locators.get("resume_path", [])
        resume_uploaded = False
        max_attempts = 3
        attempt = 0

        while not resume_uploaded and attempt < max_attempts:
            attempt += 1
            print(f"Attempting resume upload (attempt {attempt}/{max_attempts})")

            for selector in resume_selectors:
                try:
                    if selector["type"] == "css":
                        resume_input = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, selector["value"])
                            )
                        )
                    elif selector["type"] == "xpath":
                        resume_input = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH, selector["value"])
                            )
                        )
                    else:
                        continue

                    # Make the input visible and enabled
                    driver.execute_script(
                        "arguments[0].style.display='block'; "
                        "arguments[0].style.visibility='visible'; "
                        "arguments[0].style.opacity='1'; "
                        "arguments[0].style.zIndex='9999'; "
                        "arguments[0].classList.remove('invisible-resume-upload'); "
                        "arguments[0].removeAttribute('disabled');",
                        resume_input,
                    )

                    absolute_resume_path = os.path.abspath(
                        credentials.get("resume", "")
                    )
                    if not os.path.exists(absolute_resume_path):
                        print(f"Resume file not found at: {absolute_resume_path}")
                        continue

                    resume_input.send_keys(absolute_resume_path)
                    time.sleep(2)

                    # Check for upload confirmation
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, ".filename:not(:empty)")
                            )
                        )
                        resume_uploaded = True
                        print("Resume uploaded successfully")
                        break
                    except TimeoutException:
                        continue

                except Exception:
                    continue

            if not resume_uploaded:
                time.sleep(3)

        if not resume_uploaded:
            print("Could not upload resume after multiple attempts")
            user_input = input("Resume upload failed. Continue without resume? (y/n): ")
            if user_input.lower() != "y":
                print("Skipping this application")
                log_result_to_csv(
                    results_filename, url, "Skipped - Resume upload failed"
                )
                return

        # Fill personal information fields
        fields = locators.get("FIELD_SELECTORS", {})
        filled_fields = set()

        for field_name, selectors in fields.items():
            if field_name in ["resume", "resume_path"]:
                continue
            if field_name not in credentials or field_name in filled_fields:
                continue

            value = credentials.get(field_name, "")
            if not value:
                continue

            selectors = selectors if isinstance(selectors, list) else [selectors]

            for selector in selectors:
                try:
                    if selector["type"] == "css":
                        element = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, selector["value"])
                            )
                        )
                    elif selector["type"] == "xpath":
                        element = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located(
                                (By.XPATH, selector["value"])
                            )
                        )
                    else:
                        continue

                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    element.clear()
                    element.send_keys(value)
                    filled_fields.add(field_name)
                    break
                except Exception:
                    continue

        # Handle location dropdown
        try:
            location_selectors = locators.get("LOCATION_SELECTORS", {}).get("input", [])
            for selector in location_selectors:
                try:
                    if selector["type"] == "css":
                        location_input = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, selector["value"])
                            )
                        )
                    elif selector["type"] == "xpath":
                        location_input = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located(
                                (By.XPATH, selector["value"])
                            )
                        )
                    else:
                        continue

                    location_value = credentials.get("location", "")
                    if location_value:
                        driver.execute_script(
                            "arguments[0].scrollIntoView(true);", location_input
                        )
                        location_input.click()
                        location_input.clear()
                        location_input.send_keys(location_value)
                        time.sleep(1)

                        try:
                            options = WebDriverWait(driver, 5).until(
                                EC.presence_of_all_elements_located(
                                    (By.CSS_SELECTOR, "div[role='option']")
                                )
                            )
                            for option in options:
                                if location_value.lower() in option.text.lower():
                                    option.click()
                                    break
                        except TimeoutException:
                            pass

                except Exception:
                    continue
        except Exception:
            pass

        # Fill custom questions
        question_selectors = locators.get("QUESTION_SELECTORS", [])
        for selector in question_selectors:
            try:
                if selector["type"] == "css":
                    questions = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, selector["value"])
                        )
                    )
                elif selector["type"] == "xpath":
                    questions = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, selector["value"])
                        )
                    )
                else:
                    continue

                for question in questions:
                    try:
                        label = question.find_element(
                            By.CSS_SELECTOR, "div.application-label"
                        )
                        question_text = label.text.strip()
                        normalized_question = normalize_text(question_text)

                        if normalized_question in qa_pairs:
                            answer = qa_pairs[normalized_question]
                            textarea = question.find_element(
                                By.CSS_SELECTOR, "textarea"
                            )
                            driver.execute_script(
                                "arguments[0].scrollIntoView(true);", textarea
                            )
                            textarea.clear()
                            textarea.send_keys(answer)
                    except Exception:
                        continue
            except Exception:
                continue

        # Check for required fields
        required_fields = []
        try:
            required_indicators = locators.get("QUESTION_FIELD_SELECTORS", {}).get(
                "required_indicator", []
            )
            for indicator in required_indicators:
                if indicator["type"] == "text":
                    elements = driver.find_elements(
                        By.XPATH, f"//*[contains(text(), '{indicator['value']}')]"
                    )
                    for element in elements:
                        field = element.find_element(
                            By.XPATH,
                            "./ancestor::div[contains(@class, 'application-field')]",
                        )
                        required_fields.append(field)
        except Exception:
            pass

        # Verify required fields are filled
        unfilled_required = []
        for field in required_fields:
            try:
                input_element = field.find_element(
                    By.CSS_SELECTOR, "input, textarea, select"
                )
                if not input_element.get_attribute("value"):
                    label = field.find_element(
                        By.CSS_SELECTOR, "label, div.application-label"
                    )
                    unfilled_required.append(label.text.strip())
            except Exception:
                continue

        if unfilled_required:
            print("\nThe following required fields are not filled:")
            for field in unfilled_required:
                print(f"- {field}")
            print(
                "\nPlease fill these required fields manually. Press Enter when done..."
            )
            input()

        # Submit the application
        submit_selectors = locators.get("SUBMIT_SELECTORS", [])
        for selector in submit_selectors:
            try:
                if selector["type"] == "css":
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector["value"]))
                    )
                elif selector["type"] == "xpath":
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector["value"]))
                    )
                else:
                    continue

                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", submit_button
                )
                time.sleep(1)

                try:
                    driver.execute_script("arguments[0].click();", submit_button)
                    print("Application submitted successfully")
                    log_result_to_csv(results_filename, url, "Success")
                    break
                except Exception:
                    try:
                        submit_button.click()
                        print("Application submitted successfully")
                        log_result_to_csv(results_filename, url, "Success")
                        break
                    except Exception:
                        continue

            except Exception:
                continue

        # Wait before next application
        time.sleep(5)

    except Exception as e:
        print(f"Error while submitting: {e}")
        log_result_to_csv(results_filename, url, "Failed")


def run_jobvite_automation(answers_file, locators_file, resume_file, credentials_file):
    """Run the Jobvite automation."""
    logging.info("Running Jobvite automation...")

    # Load credentials from YAML
    credentials = load_credentials(f"credentials/{select_user_credentials()}")

    # Load locators
    locators = load_locators(f"locators/jobvite_locators.json")

    # Load QA pairs from jobvite_answers.csv
    qa_pairs = load_answers(f"config/jobvite_answers.csv")

    # Ensure the resume file path is absolute
    resume_file = os.path.abspath(resume_file)

    # Set up WebDriver using undetected_chromedriver
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = uc.Chrome(options=options, service=service)
    wait = WebDriverWait(driver, 20)

    # Load job URLs
    job_urls = load_job_urls(platform="jobvite")

    for job_data in job_urls:
        job_url = job_data["url"]
        company = job_data["company"]
        job_id = job_data["job_id"]

        if "jobvite" not in job_url.lower():
            continue

        try:
            logging.info(f"Opening job link: {job_url}")
            logging.info(f"Company: {company}, Job ID: {job_id}")
            driver.get(job_url)
            time.sleep(3)  # Give page time to load

            # Wait for and click Apply button
            apply_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//a[contains(text(), 'Apply') or contains(@class, 'apply-button')]",
                    )
                )
            )
            apply_button.click()
            logging.info("Clicked Apply button.")
            time.sleep(5)

            # Fill personal information from YAML
            fill_personal_info(driver, credentials)

            # Upload resume
            upload_resume(driver, resume_file)

            # Fill form fields from CSV and YAML
            filled_fields = set()
            filled_locators = set()
            fill_form(driver, qa_pairs, credentials, filled_fields, filled_locators)

            # Submit application
            submit_application(driver)

            logging.info(f"Successfully applied to job: {job_url}")

        except Exception as e:
            logging.error(f"Error applying to {job_url}: {str(e)}")
            continue

    driver.quit()


def upload_resume(driver, resume_file):
    """Upload resume file."""
    try:
        resume_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        resume_input.send_keys(resume_file)
        logging.info("Resume uploaded successfully")
    except Exception as e:
        logging.error(f"Error uploading resume: {str(e)}")


def fill_form(driver, qa_pairs, credentials, filled_fields, filled_locators):
    """Fill form fields with provided question-answer data."""
    completed_questions = set()

    for question, answer in qa_pairs.items():
        if question in filled_fields:
            logging.info(f"Skipping already filled question: {question}")
            continue

        try:
            label_xpath = f"//label[contains(normalize-space(), '{question}')] | //legend[contains(normalize-space(), '{question}')]"
            label_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, label_xpath))
            )

            # Handle radio buttons
            radio_buttons = label_element.find_elements(
                By.XPATH, "following::input[@type='radio']"
            )
            if radio_buttons:
                for rb in radio_buttons:
                    if (
                        rb.get_attribute("value").strip().lower()
                        == answer.strip().lower()
                    ):
                        driver.execute_script("arguments[0].click();", rb)
                        completed_questions.add(question)
                        filled_fields.add(question)
                        break
                continue

            # Handle other input types
            input_element = None
            try:
                input_element = label_element.find_element(
                    By.XPATH,
                    "following::*[self::input or self::textarea or self::select][1]",
                )
            except NoSuchElementException:
                continue

            if input_element:
                tag_name = input_element.tag_name.lower()
                if tag_name in ["input", "textarea"]:
                    if input_element.get_attribute("value").strip():
                        logging.info(f"Skipping already filled field: {question}")
                        filled_fields.add(question)
                        continue

                    input_element.clear()
                    input_element.send_keys(answer)

                elif tag_name == "select":
                    select = Select(input_element)
                    select.select_by_visible_text(answer)

                completed_questions.add(question)
                filled_fields.add(question)

        except Exception as e:
            logging.warning(
                f"Skipping question '{question}' - Element not found or error: {e}"
            )

    # Fill additional fields from credentials if not already filled
    for key, value in credentials.items():
        if key in filled_fields:
            continue

        try:
            field = driver.find_element(By.ID, key)
            field.clear()
            field.send_keys(value)
            logging.info(f"Filled {key} from credentials.")
            filled_fields.add(key)
        except NoSuchElementException:
            logging.warning(f"Field {key} not found in the form.")

    if len(completed_questions) == len(qa_pairs):
        logging.info("All questions have been filled successfully")

    filled_locators.update(filled_fields)


def fill_personal_info(driver, config):
    """Fill personal information from YAML config."""
    try:
        # Common personal info fields
        field_mappings = {
            "first_name": config.get("first_name", ""),
            "last_name": config.get("last_name", ""),
            "email": config.get("email", ""),
            "phone": config.get("phone", ""),
            "linkedin": config.get("linkedin", ""),
            "location": config.get("location", ""),
        }

        for field_id, value in field_mappings.items():
            try:
                field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.NAME, field_id))
                )
                field.clear()
                field.send_keys(value)
                logging.info(f"Filled {field_id}")
            except:
                logging.debug(f"Field {field_id} not found or not fillable")

    except Exception as e:
        logging.error(f"Error filling personal info: {str(e)}")


def submit_application(driver):
    """Submit the job application."""
    try:
        submit_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(text(), 'Submit') or contains(@type, 'submit')]",
                )
            )
        )
        submit_button.click()
        logging.info("Application submitted successfully")
        time.sleep(3)  # Wait for submission to complete
    except Exception as e:
        logging.error(f"Error submitting application: {str(e)}")


def main():
    # Step 1: Select the application
    application = select_application()
    print(f"Selected application: {application}")

    # Step 2: Select user credentials
    user_credentials_file = select_user_credentials()
    print(f"Selected credentials: {user_credentials_file}")

    # Step 3: Load the configuration files
    answers, locators, credentials = load_config_files(
        application, user_credentials_file
    )
    if not all([answers, locators, credentials]):
        print("Failed to load configuration files. Exiting.")
        sys.exit(1)

    # Step 4: Load job URLs
    job_urls = load_job_urls("jobs/linkedin_jobs.csv", application)
    if not job_urls:
        print("No job URLs found. Exiting.")
        sys.exit(1)

    # Step 5: Initialize WebDriver
    try:
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"Failed to initialize WebDriver: {e}")
        sys.exit(1)

    try:
        # Step 6: Run the appropriate automation
        if application == "greenhouse":
            run_greenhouse_automation(
                answers, locators, credentials["resume"], user_credentials_file
            )
        elif application == "lever":
            run_lever_automation(
                answers, locators, credentials["resume"], user_credentials_file
            )
        elif application == "jobvite":
            run_jobvite_automation(
                answers, locators, credentials["resume"], user_credentials_file
            )
    except Exception as e:
        print(f"Error during automation: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
