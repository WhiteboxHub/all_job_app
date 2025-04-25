import os
import sys
import yaml
import pandas as pd
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
import csv
import time
import random
import glob
from fuzzywuzzy import fuzz
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_config(app_name):
    config_path = f"config/{app_name}_answers.csv"
    if os.path.exists(config_path):
        return pd.read_csv(config_path)
    else:
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)


def load_locators(app_name):
    locators_path = f"locators/{app_name}_locators.json"
    if os.path.exists(locators_path):
        with open(locators_path, "r") as file:
            return json.load(file)
    else:
        logging.error(f"Locators file not found: {locators_path}")
        sys.exit(1)


def load_credentials(file_name):
    credentials_path = f"credentials/{file_name}"
    if os.path.exists(credentials_path):
        with open(credentials_path, "r") as file:
            return yaml.safe_load(file)
    else:
        logging.error(f"Credentials file not found: {credentials_path}")
        sys.exit(1)


def load_jobs():
    jobs_path = "jobs/linkedin_jobs.csv"
    if os.path.exists(jobs_path):
        return pd.read_csv(jobs_path)
    else:
        logging.error(f"Jobs file not found: {jobs_path}")
        sys.exit(1)


def load_resume(app_name, username):
    if app_name == "jobvite":
        resume_path = f"resume/{username}.txt"
    else:
        resume_path = f"resume/{username}.pdf"

    if os.path.exists(resume_path):
        return os.path.abspath(resume_path)
    else:
        logging.error(f"Resume file not found: {resume_path}")
        sys.exit(1)


def setup_logging(app_name):
    log_filename = f"logs/job_application_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def list_user_configs():
    config_dir = "credentials"
    config_files = [f for f in os.listdir(config_dir) if f.endswith(".yaml")]
    if not config_files:
        logging.error("No user configuration files found.")
        sys.exit(1)

    print("Available user configurations:")
    for idx, config_file in enumerate(config_files, start=1):
        print(f"{idx}. {config_file}")

    return config_files


def select_user_config(config_files):
    try:
        choice = int(input("Select a user configuration by number: "))
        if 1 <= choice <= len(config_files):
            return config_files[choice - 1]
        else:
            logging.error("Invalid selection.")
            sys.exit(1)
    except ValueError:
        logging.error("Invalid input. Please enter a number.")
        sys.exit(1)


def run_greenhouse(config, locators, credentials, jobs, resume):
    logging.info("Running Greenhouse application...")

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

    def load_qa_pairs(filename="config/greenhouse_answers.csv"):
        qa_pairs = {}
        if not os.path.exists(filename):
            print(f"Error: The file '{filename}' was not found.")
            return qa_pairs
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    question = row[0].strip()
                    answer = row[1].strip()
                    qa_pairs[normalize_text(question)] = answer
        return qa_pairs

    def random_sleep(min_time=2, max_time=8):
        sleep_time = random.uniform(min_time, max_time)
        print(f"Sleeping for {round(sleep_time, 2)} seconds")
        time.sleep(sleep_time)

    def log_result_to_csv(filename, url, status):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([url, status, timestamp])

    def initialize_csv(filename):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["URL", "Status", "Timestamp"])

    def apply_greenhouse(driver, url, qa_pairs, locators, user_config):
        print(f"\n🔹 Applying to: {url}")
        driver.get(url)
        random_sleep()

        try:
            apply_button_selectors = locators.get("apply_buttons", [])
            apply_button_clicked = False
            for selector in apply_button_selectors:
                try:
                    apply_button = driver.find_element(By.XPATH, selector)
                    driver.execute_script(
                        "arguments[0].scrollIntoView();", apply_button
                    )
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
                    field.send_keys(user_config[key])
                    print(f"{key} filled.")
                except NoSuchElementException:
                    print(f"{key} field not found. It might be optional.")

            random_sleep()

            try:
                location_input = driver.find_element(
                    By.ID, locators.get("location_input", "")
                )
                location_input.clear()
                location_input.send_keys(user_config["location"])
                time.sleep(2)
                location_input.send_keys(Keys.ARROW_DOWN)
                location_input.send_keys(Keys.RETURN)
                print(f"Location set to {user_config['location']} (dropdown selected)")
            except NoSuchElementException:
                print("Location input field not found. Skipping.")

            random_sleep()

            try:
                resume_input = driver.find_element(
                    By.CSS_SELECTOR, locators.get("resume_input", "")
                )
                driver.execute_script("arguments[0].scrollIntoView();", resume_input)
                resume_input.send_keys(resume)
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
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(2)
                    submit_button_clicked = False
                    for selector in submit_button_selectors:
                        try:
                            submit_button = driver.find_element(
                                By.CSS_SELECTOR, selector
                            )
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
                    confirmation_message = driver.find_element(
                        By.XPATH, confirmation_xpath
                    )
                    if confirmation_message:
                        print("Application submitted (confirmation message found).")
                        log_result_to_csv(results_filename, url, "Success")
                except NoSuchElementException:
                    print("Submission failed.")
                    log_result_to_csv(results_filename, url, "Failed")

        except Exception as e:
            print(f"Error while submitting: {e}")
            log_result_to_csv(results_filename, url, "Failed")

    # Use the credentials and resume passed from main()
    user_config = credentials
    username = os.path.splitext(os.path.basename(resume))[0]

    logs_directory = "logs"
    os.makedirs(logs_directory, exist_ok=True)
    today_date = datetime.now().strftime("%Y-%m-%d")
    results_filename = os.path.join(
        logs_directory, f"job_application_{username}_{today_date}.csv"
    )
    initialize_csv(results_filename)

    job_urls = load_job_urls()
    qa_pairs = load_qa_pairs()
    # Use the locators passed from main() instead of loading them again
    print(f"\nFound {len(job_urls)} job(s) to apply for.\n")

    for index, job_url in enumerate(job_urls, start=1):
        print(f"\nApplying for job {index}/{len(job_urls)}: {job_url}")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        try:
            apply_greenhouse(driver, job_url, qa_pairs, locators, user_config)
        except Exception as e:
            print(f"Error applying to {job_url}: {e}")
            log_result_to_csv(results_filename, job_url, "Failed")
        driver.quit()
        random_sleep()

    print("All applications completed!")


def run_jobvite(config, locators, credentials, jobs, resume):
    logging.info("Running Jobvite application...")

    # Initialize constants and variables
    applied_jobs_file = "applied_jobs.yaml"
    job_csv_file = "jobs/linkedin_jobs.csv"
    csv_file = "config/jobvite_answers.csv"
    BASE_URL = "https://jobs.jobvite.com"

    # Print credntials directly
    logging.info("========== CREDENTIALS (YAML) VALUES ==========")
    for key, value in credentials.items():
        logging.info(f"Credentials: '{key}' = '{value}'")
    logging.info("==============================================")

    def get_logger():
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        date_str = datetime.now().strftime("%d-%m-%Y")
        log_filename = f"{date_str}.log"
        log_file_path = os.path.join(log_dir, log_filename)
        logger = logging.getLogger("JobStatusLogger")

        if not logger.handlers:
            logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler(
                log_file_path, mode="a", encoding="utf-8"
            )
            formatter = logging.Formatter("%(message)s")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def logger_log_job_status(job_link, status):
        logger = get_logger()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}], {status}, {job_link}"
        logger.info(log_entry)

    def load_applied_jobs():
        if os.path.exists(applied_jobs_file):
            with open(applied_jobs_file, "r") as file:
                return yaml.safe_load(file) or {}
        return {}

    def save_applied_jobs(data):
        with open(applied_jobs_file, "w") as file:
            yaml.dump(data, file)

    def log_job_status(job_link, status):
        jobs_data = load_applied_jobs()
        jobs_data[job_link] = status
        save_applied_jobs(jobs_data)
        logger_log_job_status(job_link, status)

    def generate_job_links(csv_filename):
        job_links = []

        try:
            with open(csv_filename, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    company = row.get("company", "").strip()
                    job_id = row.get("job_id", "").strip()
                    fallback_url = row.get("platform_link", "").strip()
                    platform = row.get("platform", "").strip().lower()

                    final_url = None

                    if platform == "jobvite":
                        if company and job_id:
                            final_url = f"{BASE_URL}/{company}/job/{job_id}"
                        elif fallback_url:
                            final_url = fallback_url
                            logging.warning(
                                f"Falling back to platform_link for row: {row}"
                            )
                        else:
                            logging.warning(
                                f"Missing data to construct URL and no fallback: {row}"
                            )
                            continue

                        job_data = {
                            "company": company,
                            "job_id": job_id,
                            "url": final_url,
                        }
                        job_links.append(job_data)
                    else:
                        logging.info(f"Skipping non-Jobvite platform: {row}")

            logging.info(
                f"Loaded {len(job_links)} Jobvite job entries from {csv_filename}"
            )

        except FileNotFoundError:
            logging.error(f"CSV file {csv_filename} not found.")
        except Exception as e:
            logging.exception(f"Unexpected error while reading {csv_filename}: {e}")

        return job_links

    def read_csv(file_path):
        qa_dict = {}
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                question = row["question"].strip()
                answer = row["answer"].strip()
                qa_dict[question] = answer
        return qa_dict

    def fill_form(driver, qa_data, filled_fields, filled_locators):
        completed_questions = set()

        for question, answer in qa_data.items():
            if question in filled_fields:
                logging.info(f"Skipping already filled question: {question}")
                continue

            try:
                label_xpath = f"//label[contains(normalize-space(), '{question}')] | //legend[contains(normalize-space(), '{question}')]"
                label_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, label_xpath))
                )

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

        if len(completed_questions) == len(qa_data):
            logging.info(
                "------All questions have been filled. Stopping execution-----"
            )

        filled_locators.update(filled_fields)

    interacted_elements = set()

    def interact_with_element(
        driver, css_selector, element_type, value=None, filled_locators=None
    ):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            if element in interacted_elements or (
                filled_locators and css_selector in filled_locators
            ):
                return True

            existing_value = element.get_attribute("value")
            if existing_value:
                logging.info(f"Skipping already filled element: {css_selector}")
                if filled_locators is not None:
                    filled_locators.add(css_selector)
                return True

            if element_type == "input":
                element.clear()
                element.send_keys(value or "")

            elif element_type == "select":
                select = Select(element)
                try:
                    select.select_by_value(value)
                except:
                    select.select_by_visible_text(value)

            elif element_type in ["radio", "checkbox"] and not element.is_selected():
                element.click()

            elif element_type == "textarea":
                element.clear()
                element.send_keys(value)

            elif element_type == "button":
                element.click()

            interacted_elements.add(element)
            if filled_locators is not None:
                filled_locators.add(css_selector)
            return True

        except Exception as e:
            logging.error(f"Error interacting with element ({css_selector}): {e}")
            return False

    def execute_automation(driver, locators, filled_locators):
        for key, locator in locators.items():
            interact_with_element(
                driver,
                locator["selector"],
                locator["type"],
                locator.get("value", ""),
                filled_locators,
            )

    def wait_until_all_required_filled(driver):
        while True:
            required_fields = driver.find_elements(
                By.CSS_SELECTOR, "input[required], select[required], textarea[required]"
            )
            unfilled_fields = [
                field for field in required_fields if not field.get_attribute("value")
            ]

            if not unfilled_fields:
                logging.info("All required fields are filled. Proceeding...")
                return

            for field in unfilled_fields:
                logging.info(
                    f"Waiting for required field: {field.get_attribute('label') or field.get_attribute('id') or 'Unknown Field'}"
                )

            time.sleep(5)

    def handle_uninteracted_required_elements(driver, config, filled_locators):
        all_form_elements = driver.find_elements(
            By.CSS_SELECTOR, "input, select, textarea"
        )
        for element in all_form_elements:
            if element not in interacted_elements:
                try:
                    is_required = element.get_attribute("required") is not None
                    if is_required and not element.get_attribute("value"):
                        element.clear()
                        element.send_keys(config.get(element.get_attribute("name"), ""))
                        interacted_elements.add(element)
                        if filled_locators is not None:
                            filled_locators.add(element.get_attribute("name"))
                except Exception as e:
                    print(f"Error processing required element: {e}")

    def upload_resume(driver, resume_path):
        try:
            with open(resume_path, "r") as file:
                resume_text = file.read()

            paste_resume_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "span.jv-text-block.jv-text-link.needsclick.ng-binding",
                    )
                )
            )
            paste_resume_button.click()
            logging.info("Selected 'Type or Paste Resume' option.")

            textarea = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#jv-paste-resume-textarea0")
                )
            )
            textarea.clear()
            textarea.send_keys(resume_text)
            logging.info("Pasted resume text into the textarea.")

            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button.jv-button.jv-button-primary[ng-disabled='!pastedText']",
                    )
                )
            )
            save_button.click()
            logging.info("Clicked the Save button after pasting the resume.")

        except NoSuchElementException as e:
            logging.error(f"Element not found during resume upload: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def apply_to_job(driver, wait, job_id, job_link, resume_path, locators, config):
        logging.info(f"Opening job link: {job_link}")
        driver.get(job_link)

        filled_locators = set()
        filled_fields = set()

        # Convert config values to strings to avoid pandas Series issues
        string_config = {}
        for key, value in config.items():
            # Check if value is a pandas Series (which causes truth value ambiguity)
            if hasattr(value, "tolist") and callable(getattr(value, "tolist")):
                try:
                    # Convert Series to list then first item to string
                    value_list = value.tolist()
                    if value_list and len(value_list) > 0:
                        string_config[key] = str(value_list[0])
                except:
                    string_config[key] = str(value)
            else:
                string_config[key] = str(value) if value is not None else ""

        # Use the string_config instead of original config for remaining operations
        config = string_config

        # Print out all the config key-value pairs for debugging
        logging.info("========== CONFIG VALUES ==========")
        for key, value in config.items():
            logging.info(f"Config: '{key}' = '{value}'")
        logging.info("===================================")

        # Also print to stdout for better visibility
        print("\n========== JOBVITE CONFIG VALUES ==========")
        print(f"First name: '{config.get('first name', 'NOT FOUND')}'")
        print(f"Last name: '{config.get('last name', 'NOT FOUND')}'")
        print(f"Email: '{config.get('email', 'NOT FOUND')}'")
        print(f"Phone: '{config.get('phone', 'NOT FOUND')}'")
        print(f"Address: '{config.get('address', 'NOT FOUND')}'")
        print(f"City: '{config.get('city', 'NOT FOUND')}'")
        print(f"State: '{config.get('state', 'NOT FOUND')}'")
        print(f"Zip: '{config.get('zip', 'NOT FOUND')}'")
        print(f"Country: '{config.get('country', 'NOT FOUND')}'")
        print(f"Job Posting: '{config.get('job posting', 'NOT FOUND')}'")
        print("============================================\n")

        try:
            # Click the apply button to start the application
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

            # Identify all required form fields for logging purposes
            elements = driver.find_elements(By.XPATH, '//*[@required="required"]')
            for element in elements:
                element_id = element.get_attribute("id")
                element_value = element.get_attribute("value") or element.get_attribute(
                    "name"
                )
                autocomplete_attr = element.get_attribute("autocomplete")

                print(
                    f"ID: {element_id}, Value: {element_value}, Autocomplete: {autocomplete_attr}"
                )

                label = None
                for i in range(1, 6):
                    label_xpath = f"./ancestor::*[{i}]/label"
                    label_element = element.find_elements(By.XPATH, label_xpath)
                    if label_element:
                        label = label_element[0].text
                        break

                label_text = label if label else "No label found"
                print(
                    f"ID: {element_id}, Value: {element_value}, Nearest Label: {label_text}"
                )

            # ----- UPLOAD RESUME FIRST -----

            logging.info("Looking for resume upload button...")
            try:
                # First try to find and click the resume upload select button
                try:
                    select_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Select')]")
                        )
                    )
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", select_button
                    )
                    time.sleep(1)
                    select_button.click()
                    logging.info("Clicked Select button for resume upload.")
                except Exception as e:
                    logging.warning(
                        f"Could not find 'Select' button, trying alternative methods: {e}"
                    )
                    try:
                        # Try alternative resume upload button
                        upload_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable(
                                (
                                    By.XPATH,
                                    "//button[contains(@class, 'resume') and contains(@class, 'upload')]",
                                )
                            )
                        )
                        upload_btn.click()
                        logging.info("Clicked alternative resume upload button")
                    except:
                        # Try to find file input directly
                        logging.info("Trying to find file input element directly")
                        file_inputs = driver.find_elements(
                            By.XPATH, "//input[@type='file']"
                        )
                        if file_inputs:
                            driver.execute_script(
                                "arguments[0].style.display = 'block';", file_inputs[0]
                            )
                            file_inputs[0].send_keys(resume_path)
                            logging.info(
                                f"Directly uploaded resume to file input: {resume_path}"
                            )

                # Upload the resume using the function
                time.sleep(2)
                upload_resume(driver, resume_path)
                logging.info(f"Uploaded resume: {resume_path}")
                time.sleep(5)  # Wait longer for resume to process

                # ----- VERIFY AND RE-FILL FIELDS AFTER RESUME UPLOAD -----
                logging.info(
                    "VERIFYING fields after resume upload (resume may have overwritten them)"
                )

                # Re-apply force fill to make sure resume didn't override our values
                for label_text, value in force_fields.items():
                    if not value:
                        continue

                    logging.info(f"Verifying '{label_text}' still has value '{value}'")

                    # Try multiple approaches to find the field
                    found = False

                    # 1. Try by exact label text
                    try:
                        # First try exact label match
                        label_xpath = f"//label[text()='{label_text}' or text()='{label_text}*' or contains(text(), '{label_text}')]"
                        labels = driver.find_elements(By.XPATH, label_xpath)

                        if labels:
                            for label in labels:
                                try:
                                    # Try by 'for' attribute (most reliable)
                                    if label.get_attribute("for"):
                                        input_id = label.get_attribute("for")
                                        input_element = driver.find_element(
                                            By.ID, input_id
                                        )

                                        # Check if current value matches our config
                                        current_value = input_element.get_attribute(
                                            "value"
                                        )
                                        if (
                                            input_element.tag_name != "select"
                                            and current_value != value
                                        ):
                                            logging.info(
                                                f"⚠️ Field '{label_text}' was changed by resume to '{current_value}', restoring to '{value}'"
                                            )
                                            input_element.clear()
                                            input_element.send_keys(value)
                                            logging.info(
                                                f"✓ Re-filled '{label_text}' with '{value}'"
                                            )

                                        found = True
                                        break
                                    else:
                                        # Try finding nearest input
                                        input_xpath = "following::*[self::input or self::textarea or self::select][1]"
                                        input_elements = label.find_elements(
                                            By.XPATH, input_xpath
                                        )

                                        if input_elements:
                                            input_element = input_elements[0]

                                            # Check if current value matches our config
                                            current_value = input_element.get_attribute(
                                                "value"
                                            )
                                            if (
                                                input_element.tag_name != "select"
                                                and current_value != value
                                            ):
                                                logging.info(
                                                    f"⚠️ Field '{label_text}' was changed by resume to '{current_value}', restoring to '{value}'"
                                                )
                                                input_element.clear()
                                                input_element.send_keys(value)
                                                logging.info(
                                                    f"✓ Re-filled '{label_text}' with '{value}'"
                                                )

                                            found = True
                                            break
                                except Exception as e:
                                    logging.debug(f"Error verifying {label_text}: {e}")
                                    continue
                    except Exception as e:
                        logging.debug(f"Error with label verification: {e}")

                    # 2. If not found by label, try by placeholder, name, or id
                    if not found:
                        # Remove spaces and convert to lowercase for matching
                        field_match = (
                            label_text.lower().replace(" ", "").replace("/", "")
                        )
                        try:
                            # Try various attributes
                            for attr in ["placeholder", "name", "id", "aria-label"]:
                                xpath = f"//*[@{attr} and contains(translate(@{attr}, ' /ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_match.lower()}')]"
                                elements = driver.find_elements(By.XPATH, xpath)

                                if elements:
                                    for element in elements:
                                        if (
                                            element.is_displayed()
                                            and element.is_enabled()
                                        ):
                                            # Check if current value matches our config
                                            current_value = element.get_attribute(
                                                "value"
                                            )
                                            if (
                                                element.tag_name != "select"
                                                and current_value != value
                                            ):
                                                logging.info(
                                                    f"⚠️ Field '{label_text}' was changed by resume to '{current_value}', restoring to '{value}'"
                                                )
                                                element.clear()
                                                element.send_keys(value)
                                                logging.info(
                                                    f"✓ Re-filled '{label_text}' with '{value}'"
                                                )

                                            found = True
                                            break

                            if found:
                                break
                        except Exception as e:
                            logging.debug(f"Error with attribute verification: {e}")

            except Exception as e:
                logging.error(f"Failed to upload resume: {e}")

            # ----- NOW FILL FORM FIELDS FROM CONFIG AND LOCATORS -----

            # Load question-answer data from CSV
            qa_data = read_csv(csv_file)

            logging.info("Filling form fields from config and locators")

            # FORCE FILL specific fields identified in the example with YAML values
            # This ensures these exact fields are filled from YAML no matter what
            force_fields = {
                "First Name": credentials.get(
                    "first name", ""
                ),  # Get directly from credentials
                "First": credentials.get(
                    "first name", ""
                ),  # Get directly from credentials
                "Last Name": credentials.get(
                    "last name", ""
                ),  # Get directly from credentials
                "Last/Surname Name": credentials.get(
                    "last name", ""
                ),  # Get directly from credentials
                "Last": credentials.get(
                    "last name", ""
                ),  # Get directly from credentials
                "Email": credentials.get("email", ""),  # Get directly from credentials
                "Address": credentials.get(
                    "address", ""
                ),  # Get directly from credentials
                "City": credentials.get("city", ""),  # Get directly from credentials
                "State": credentials.get("state", ""),  # Get directly from credentials
                "Zip": credentials.get("zip", ""),  # Get directly from credentials
                "Country": credentials.get(
                    "country", ""
                ),  # Get directly from credentials
                "Phone": credentials.get("phone", ""),  # Get directly from credentials
                "How did you hear about this Job": credentials.get(
                    "job posting", "LinkedIn Job Posting"
                ),
                "How did you hear about this job": credentials.get(
                    "job posting", "LinkedIn Job Posting"
                ),
                "Preferred First Name": credentials.get(
                    "your name", credentials.get("first name", "")
                ),
                "Gender": credentials.get("gender", ""),
                "Pronouns": credentials.get("pronouns", ""),
                "Work Status": credentials.get("work status", ""),
                "Work Authorization": credentials.get("work authorization", ""),
            }

            # Also print the force fields for debugging
            print("\n========== FORCE FIELDS VALUES (FROM CREDENTIALS) ==========")
            for field, value in force_fields.items():
                if value:  # Only print non-empty values
                    print(f"{field}: '{value}'")
            print("=====================================================\n")

            # Force fill these fields by finding exact label matches and filling them
            logging.info("FORCE FILLING fields from YAML config")
            for label_text, value in force_fields.items():
                if not value:
                    continue

                logging.info(f"Force filling '{label_text}' with '{value}'")

                # Try multiple approaches to find the field
                found = False

                # 1. Try by exact label text
                try:
                    # First try exact label match
                    label_xpath = f"//label[text()='{label_text}' or text()='{label_text}*' or contains(text(), '{label_text}')]"
                    labels = driver.find_elements(By.XPATH, label_xpath)

                    if labels:
                        for label in labels:
                            try:
                                # Try by 'for' attribute (most reliable)
                                if label.get_attribute("for"):
                                    input_id = label.get_attribute("for")
                                    input_element = driver.find_element(By.ID, input_id)

                                    if input_element.tag_name == "select":
                                        select = Select(input_element)
                                        try:
                                            select.select_by_visible_text(value)
                                            logging.info(
                                                f"✓ Force filled '{label_text}' with '{value}' by label.for"
                                            )
                                            found = True
                                            break
                                        except:
                                            continue
                                    else:
                                        # Always clear and enter value to override
                                        input_element.clear()
                                        input_element.send_keys(value)
                                        logging.info(
                                            f"✓ Force filled '{label_text}' with '{value}' by label.for"
                                        )
                                        found = True
                                        break
                                else:
                                    # Try finding nearest input
                                    input_xpath = "following::*[self::input or self::textarea or self::select][1]"
                                    input_elements = label.find_elements(
                                        By.XPATH, input_xpath
                                    )

                                    if input_elements:
                                        input_element = input_elements[0]
                                        if input_element.tag_name == "select":
                                            select = Select(input_element)
                                            try:
                                                select.select_by_visible_text(value)
                                                logging.info(
                                                    f"✓ Force filled '{label_text}' with '{value}' by following::"
                                                )
                                                found = True
                                                break
                                            except:
                                                continue
                                        else:
                                            # Always clear and enter value to override
                                            input_element.clear()
                                            input_element.send_keys(value)
                                            logging.info(
                                                f"✓ Force filled '{label_text}' with '{value}' by following::"
                                            )
                                            found = True
                                            break
                            except Exception as e:
                                logging.debug(f"Error forcing {label_text}: {e}")
                                continue
                except Exception as e:
                    logging.debug(f"Error with label search: {e}")

                # 2. If not found, try by placeholder, name, or id that contains the field name
                if not found:
                    # Remove spaces and convert to lowercase for matching
                    field_match = label_text.lower().replace(" ", "").replace("/", "")
                    try:
                        # Try various attributes
                        for attr in ["placeholder", "name", "id", "aria-label"]:
                            xpath = f"//*[@{attr} and contains(translate(@{attr}, ' /ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{field_match.lower()}')]"
                            elements = driver.find_elements(By.XPATH, xpath)

                            if elements:
                                for element in elements:
                                    if element.is_displayed() and element.is_enabled():
                                        if element.tag_name == "select":
                                            select = Select(element)
                                            try:
                                                select.select_by_visible_text(value)
                                                logging.info(
                                                    f"✓ Force filled '{label_text}' with '{value}' by {attr}"
                                                )
                                                found = True
                                                break
                                            except:
                                                continue
                                        else:
                                            # Always clear and enter value to override
                                            element.clear()
                                            element.send_keys(value)
                                            logging.info(
                                                f"✓ Force filled '{label_text}' with '{value}' by {attr}"
                                            )
                                            found = True
                                            break

                            if found:
                                break
                    except Exception as e:
                        logging.debug(f"Error with attribute search: {e}")

            # Now continue with the regular filling approaches
            # 1. First try to fill common form fields directly by ID or name
            logging.info("Direct approach - filling fields by ID/attribute mappings")
            field_mappings = {
                "first_name": ["first", "firstname", "fname", "given-name"],
                "last_name": ["last", "lastname", "lname", "family-name"],
                "email": ["email", "emailaddress"],
                "phone": ["phone", "phonenumber", "tel"],
                "address": ["address", "streetaddress", "street", "address-line1"],
                "city": ["city", "cityname", "address-level2"],
                "state": ["state", "stateprovince", "address-level1"],
                "zip": ["zip", "zipcode", "postalcode", "postal", "postal-code"],
                "country": ["country", "countryname", "country-name"],
            }

            # Look for these fields and fill them
            for config_key, search_terms in field_mappings.items():
                if config_key in config and config[config_key]:
                    value = config[config_key]
                    # Try each possible match for the field
                    for term in search_terms:
                        try:
                            # Try different attribute selectors
                            for attr in ["id", "name", "placeholder", "autocomplete"]:
                                xpath = f"//*[contains(@{attr}, '{term}')]"
                                elements = driver.find_elements(By.XPATH, xpath)

                                if elements:
                                    for element in elements:
                                        try:
                                            if (
                                                element.is_displayed()
                                                and element.is_enabled()
                                            ):
                                                tag_name = element.tag_name.lower()
                                                if tag_name == "select":
                                                    select = Select(element)
                                                    try:
                                                        select.select_by_visible_text(
                                                            value
                                                        )
                                                        logging.info(
                                                            f"Filled {config_key} with '{value}' (select)"
                                                        )
                                                        filled_fields.add(config_key)
                                                        break
                                                    except:
                                                        # Try first option that's not empty
                                                        for option in select.options:
                                                            if option.text.strip() and option.text.strip().lower() not in [
                                                                "select",
                                                                "choose",
                                                            ]:
                                                                select.select_by_visible_text(
                                                                    option.text
                                                                )
                                                                logging.info(
                                                                    f"Filled {config_key} with fallback option '{option.text}'"
                                                                )
                                                                filled_fields.add(
                                                                    config_key
                                                                )
                                                                break
                                                else:
                                                    element.clear()
                                                    element.send_keys(value)
                                                    logging.info(
                                                        f"Filled {config_key} with '{value}'"
                                                    )
                                                    filled_fields.add(config_key)
                                                    break
                                        except:
                                            continue

                                if config_key in filled_fields:
                                    break
                        except Exception as e:
                            logging.debug(f"Error filling {config_key}: {e}")

                        if config_key in filled_fields:
                            break

            # 2. Fill using label text to find fields
            logging.info("Filling fields by finding labels")
            for key, value in config.items():
                # Skip empty values or if field already filled
                if not value or key in filled_fields:
                    continue

                # Try to find field by label text (exact match first, then contains)
                for match_type in ["equals", "contains"]:
                    try:
                        label_xpath = (
                            f"//label[text()='{key}']"
                            if match_type == "equals"
                            else f"//label[contains(text(), '{key}')]"
                        )
                        labels = driver.find_elements(By.XPATH, label_xpath)

                        for label in labels:
                            try:
                                # Try to find the input near this label
                                input_element = None

                                # Try by for attribute
                                if label.get_attribute("for"):
                                    input_id = label.get_attribute("for")
                                    input_element = driver.find_element(By.ID, input_id)
                                else:
                                    # Try finding nearest input
                                    input_element = label.find_element(
                                        By.XPATH,
                                        "following::*[self::input or self::textarea or self::select][1]",
                                    )

                                if (
                                    input_element
                                    and input_element.is_displayed()
                                    and input_element.is_enabled()
                                ):
                                    if input_element.tag_name == "select":
                                        select = Select(input_element)
                                        try:
                                            select.select_by_visible_text(value)
                                        except:
                                            # Try finding closest option
                                            for option in select.options:
                                                if (
                                                    option.text.strip()
                                                    and option.text.strip().lower()
                                                    != "select"
                                                ):
                                                    select.select_by_visible_text(
                                                        option.text
                                                    )
                                                    break
                                    else:
                                        input_element.clear()
                                        input_element.send_keys(value)

                                    logging.info(
                                        f"Filled field '{key}' with value '{value}' by label"
                                    )
                                    filled_fields.add(key)
                                    break
                            except Exception as e:
                                logging.debug(f"Error with label '{key}': {e}")
                                continue

                        if key in filled_fields:
                            break
                    except Exception as e:
                        logging.debug(f"Could not fill field '{key}' by label: {e}")

                # If field still not filled, try common variations of the key
                if key not in filled_fields:
                    variations = [
                        key,
                        key.replace("_", " "),
                        key.replace("_", "-"),
                        key.title(),
                        key.upper(),
                    ]

                    for var in variations:
                        try:
                            xpath = f"//label[contains(text(), '{var}')]"
                            labels = driver.find_elements(By.XPATH, xpath)
                            if labels:
                                for label in labels:
                                    # Similar process as above
                                    try:
                                        input_xpath = "following::*[self::input or self::textarea or self::select][1]"
                                        input_element = label.find_element(
                                            By.XPATH, input_xpath
                                        )

                                        if (
                                            input_element.is_displayed()
                                            and input_element.is_enabled()
                                        ):
                                            if input_element.tag_name == "select":
                                                select = Select(input_element)
                                                try:
                                                    select.select_by_visible_text(value)
                                                except:
                                                    continue
                                            else:
                                                input_element.clear()
                                                input_element.send_keys(value)

                                            logging.info(
                                                f"Filled field '{key}' with '{value}' using variation '{var}'"
                                            )
                                            filled_fields.add(key)
                                            break
                                    except:
                                        continue
                        except:
                            continue

                        if key in filled_fields:
                            break

            # 3. Fill the How did you hear dropdown
            logging.info("Handling the 'How did you hear about this job' dropdown")
            try:
                hear_about_xpath = "//label[contains(text(), 'hear') or contains(text(), 'How did you')]"
                labels = driver.find_elements(By.XPATH, hear_about_xpath)

                if labels:
                    for label in labels:
                        try:
                            input_xpath = "following::select[1]"
                            select_element = label.find_element(By.XPATH, input_xpath)

                            select = Select(select_element)
                            try:
                                # Try LinkedIn first
                                linkedin_options = [
                                    opt
                                    for opt in select.options
                                    if "linkedin" in opt.text.lower()
                                ]
                                if linkedin_options:
                                    select.select_by_visible_text(
                                        linkedin_options[0].text
                                    )
                                    logging.info(
                                        f"Selected 'LinkedIn' option from dropdown"
                                    )
                                else:
                                    # Otherwise select first non-empty
                                    for option in select.options:
                                        if (
                                            option.text.strip()
                                            and option.text.strip().lower()
                                            not in ["select", "choose"]
                                        ):
                                            select.select_by_visible_text(option.text)
                                            logging.info(
                                                f"Selected first non-empty option: {option.text}"
                                            )
                                            break
                            except Exception as e:
                                logging.debug(f"Error selecting option: {e}")
                        except:
                            continue
            except Exception as e:
                logging.debug(f"Error handling 'How did you hear' dropdown: {e}")


            # 5. Execute the original automation logic
            logging.info("Running original execute_automation for any remaining fields")
            execute_automation(driver, locators, filled_locators)


            # 4. Fill using CSV question-answer pairs
            logging.info("Filling using CSV question-answer pairs")
            fill_form(driver, qa_data, filled_fields, filled_locators)

            # 6. Final check for required fields
            handle_uninteracted_required_elements(driver, config, filled_locators)
            wait_until_all_required_filled(driver)

            # Continue with the rest of the application process
            try:
                next_button = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            "button.jv-button.jv-button-primary.jv-button-large",
                        )
                    )
                )
                next_button.click()
                logging.info("------Clicked Next button----")
                time.sleep(5)

                # Re-apply our config-based field filling to make sure resume didn't override anything
                # execute_automation(driver, locators, filled_locators)
                handle_uninteracted_required_elements(driver, config, filled_locators)
                fill_form(driver, qa_data, filled_fields, filled_locators)
                wait_until_all_required_filled(driver)

                # Try to find another Next button on the second page
                try:
                    next_button = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                "button.jv-button.jv-button-primary.jv-button-large",
                            )
                        )
                    )
                    next_button.click()
                    logging.info(
                        "-----Clicked the Next button proceeding to the next page-----"
                    )
                    time.sleep(5)

                    # Re-apply our field filling after going to next page
                    # execute_automation(driver, locators, filled_locators)
                    handle_uninteracted_required_elements(
                        driver, config, filled_locators
                    )
                    fill_form(driver, qa_data, filled_fields, filled_locators)
                    wait_until_all_required_filled(driver)
                except Exception as e:
                    logging.info(f"No additional Next button found or error: {e}")
                    # Will continue to Send Application button

            except Exception as e:
                logging.info(f"No Next button found: {e}")
                try:
                    send_button = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "//button[contains(@class, 'jv-button-primary') and contains(., 'Send Application')]",
                            )
                        )
                    )
                    driver.execute_script("arguments[0].click();", send_button)
                    logging.info("No Next button found, clicked Send Application.")
                except Exception as send_e:
                    logging.warning(
                        f"Could not find either Next or Send Application button: {send_e}"
                    )

            # Final send application button
            try:
                send_button = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(@class, 'jv-button-primary') and contains(., 'Send Application')]",
                        )
                    )
                )
                driver.execute_script("arguments[0].click();", send_button)
                logging.info("------Clicked 'Send Application' button-------")
                time.sleep(5)  # Wait for form submission

                try:
                    confirmation_message = wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "h2.jv-page-message-header")
                        )
                    )
                    print(
                        "---------------------Applied_Successfully----------------------------------------"
                    )
                    logging.info("Application submitted successfully!")
                    log_job_status(job_link, "Successfully Applied")

                except TimeoutException:
                    try:
                        already_applied_message = wait.until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "p.jv-page-error-header")
                            )
                        )
                        print(
                            "---------------------------already_applied----------------------------------------"
                        )
                        logging.info(
                            "-----You have already submitted the application------"
                        )
                        log_job_status(job_link, "Already Submitted")

                    except TimeoutException:
                        logging.error(
                            "Unable to submit the application and no confirmation message found."
                        )
                        log_job_status(job_link, "Submission Failed")
            except Exception as e:
                logging.error(f"Error in final application submission: {e}")
                log_job_status(job_link, "Submission Error")

        except TimeoutException:
            logging.error(f"Timeout: Could not find elements for job {job_link}")
            log_job_status(job_link, "Failed")
        except NoSuchElementException as e:
            logging.error(f"Error applying for job: {e}")
            log_job_status(job_link, "Failed")
        except Exception as e:
            logging.error(f"Unexpected error applying to {job_link}: {e}")
            log_job_status(job_link, "Failed")

    # Setup the resume path
    resume_filename = os.path.basename(resume)
    resume_path = resume  # Use the full path that was passed to the function

    logging.info(f"======== USING RESUME: {resume_path} ========")

    if not os.path.isfile(resume_path):
        logging.error(f"Resume file not found at {resume_path}")
        sys.exit(1)

    # Load locators if not already provided
    if not locators or not isinstance(locators, dict) or len(locators) == 0:
        with open("locators/jobvite_locators.json", "r") as f:
            locators = json.load(f)

    # Update locator values from config
    for key in locators.keys():
        if key in config:
            locators[key]["value"] = config[key]

    for key, locator in locators.items():
        placeholder = f"{{{{ {key.replace('_', ' ')} }}}}"
        if locator.get("value") == placeholder:
            locator["value"] = config.get(key.replace("_", " "), "")

    # Set up WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)

    # Get job list and process jobs
    applied_jobs = load_applied_jobs()
    job_links = generate_job_links(job_csv_file)

    logging.info(f"Found {len(job_links)} Jobvite jobs to process")

    try:
        for job in job_links:
            job_id = job["job_id"]
            job_link = job["url"]

            if (
                job_link in applied_jobs
                and applied_jobs[job_link] == "Successfully Applied"
            ):
                logging.info(f"Skipping already applied job: {job_id}")
                continue

            # Create a merged config that combines config and credentials
            # This ensures we have all values from credentials in the config for form filling
            merged_config = config.copy()

            # Convert pandas DataFrame config to dict if needed
            if isinstance(config, pd.DataFrame):
                # Check if it's a DataFrame and convert properly
                if len(config) > 0:
                    # Convert the first row to a dictionary
                    config_dict = config.iloc[0].to_dict()
                    merged_config = config_dict
                else:
                    merged_config = {}

            # Update with credentials values (which take precedence)
            merged_config.update(credentials)

            logging.info("Using merged config with credentials for form filling")

            apply_to_job(
                driver, wait, job_id, job_link, resume_path, locators, merged_config
            )

            # Add a short delay between job applications
            time.sleep(random.uniform(3, 7))
    except Exception as e:
        logging.error(f"Error in job application process: {e}")
    finally:
        driver.quit()
        logging.info("Jobvite application process completed")


def run_lever(config, locators, credentials, jobs, resume):
    logging.info("Running Lever application...")

    class LeverAutomation:
        def __init__(self):
            self.lever_base_url = "https://jobs.lever.co"
            self.profile_yaml = os.path.basename(resume).replace(".pdf", ".yaml")
            self.candidate_name = os.path.splitext(self.profile_yaml)[0]

            # Load necessary resources
            self.load_locators()

            # Set up credentials
            self.credentials = credentials.copy() if credentials else {}

            # Ensure resume path is absolute
            self.credentials["resume"] = os.path.abspath(resume) if resume else ""

            # Make sure we have the correct fields
            if "full_name" in self.credentials:
                name_parts = self.credentials["full_name"].split()
                if len(name_parts) > 1 and "first_name" not in self.credentials:
                    self.credentials["first_name"] = name_parts[0]
                if len(name_parts) > 1 and "last_name" not in self.credentials:
                    self.credentials["last_name"] = name_parts[-1]

            # Load answers from CSV
            self.answers = self.load_answers("config/lever_answers.csv")

            # Set up webdriver
            self.driver = self.setup_driver()

            logging.info(
                f"LeverAutomation initialized with resume: {self.credentials.get('resume', 'Not provided')}"
            )
            logging.info(f"Loaded {len(self.answers)} answers from CSV")

        def find_element(self, locator_key, sub_key=None, multiple=False, timeout=10):
            if sub_key:
                selectors = self.locators.get(locator_key, {}).get(sub_key, [])
            else:
                selectors = self.locators.get(locator_key, [])
            if not isinstance(selectors, list):
                selectors = [selectors]
            logging.info(
                f"Trying selectors for {locator_key}{'.' + sub_key if sub_key else ''}: {[s['value'] for s in selectors]}"
            )

            for selector in selectors:
                selector_type = selector.get("type", "css")
                selector_value = selector.get("value", "")
                logging.info(f"Attempting {selector_type} selector: {selector_value}")

                try:
                    by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                    if multiple:
                        return WebDriverWait(self.driver, timeout).until(
                            EC.presence_of_all_elements_located(
                                (by_type, selector_value)
                            )
                        )
                    return WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((by_type, selector_value))
                    )
                except TimeoutException:
                    logging.warning(
                        f"Timeout {selector_type} selector {selector_value}"
                    )
                    continue
                except NoSuchElementException:
                    logging.warning(
                        f"Element not found for {selector_type} selector {selector_value}"
                    )
                    continue
                except ElementNotInteractableException:
                    logging.warning(
                        f"Element not interactable for {selector_type} selector {selector_value}"
                    )
                    continue
                except Exception as e:
                    logging.warning(
                        f"Unexpected error for {selector_type} selector {selector_value}: {str(e)}"
                    )
                    continue
            logging.error(
                f"No selectors worked for {locator_key}{'.' + sub_key if sub_key else ''}"
            )
            return None

        def upload_resume(self):
            value = self.credentials["resume"]
            logging.info(f"Attempting to upload resume: {value}")

            resume_input = self.find_element("resume_path")
            if not resume_input:
                logging.warning("Resume file input not found, it may be optional")
                return False

            logging.info(
                f"Found resume input: {resume_input.get_attribute('outerHTML')}"
            )

            try:
                upload_button = self.find_element("resume_upload_button")
                if upload_button:
                    logging.info(
                        f"Upload button found: {upload_button.get_attribute('outerHTML')}"
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", upload_button
                    )
                    self.driver.execute_script("arguments[0].click();", upload_button)
                    logging.info("Clicked resume upload button")
                    time.sleep(1)
                else:
                    logging.info("No resume upload button found")
            except Exception as e:
                logging.warning(f"Failed to click upload button: {str(e)}")

            try:
                self.driver.execute_script(
                    "arguments[0].style.display='block'; "
                    "arguments[0].style.visibility='visible'; "
                    "arguments[0].style.opacity='1'; "
                    "arguments[0].style.zIndex='9999'; "
                    "arguments[0].classList.remove('invisible-resume-upload'); "
                    "arguments[0].removeAttribute('disabled');",
                    resume_input,
                )
                logging.info("Made resume input visible")
            except Exception as e:
                logging.warning(f"Failed to apply visibility script: {str(e)}")

            try:
                resume_input.send_keys(value)
                logging.info(f"Uploaded resume: {value}")
            except ElementNotInteractableException as e:
                logging.error(f"Resume input not interactable: {str(e)}")
                return False
            except Exception as e:
                logging.error(f"Failed to upload resume: {str(e)}")
                return False

            try:
                confirmation_selectors = [
                    s["value"]
                    for s in self.locators.get("resume_upload_confirmation", [])
                    if s["type"] == "css"
                ]
                if confirmation_selectors:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ", ".join(confirmation_selectors))
                        )
                    )
                    logging.info("Resume upload confirmed")
                else:
                    logging.info("No confirmation selectors defined")
            except TimeoutException:
                logging.info("No upload confirmation found")
            except Exception as e:
                logging.warning(f"Error checking upload confirmation: {str(e)}")

            time.sleep(2)
            return True

        def normalize_text(self, text):
            """Normalize text for comparison"""
            if not text:
                return ""
            return re.sub(r"[^a-zA-Z0-9\s]", "", text).strip().lower()

        def validate_required_fields(self):
            """Validate that all required fields are present in credentials"""
            required_fields = ["full_name", "email", "phone", "resume"]
            missing_fields = []

            for field in required_fields:
                if not self.credentials.get(field):
                    missing_fields.append(field)

            if missing_fields:
                logging.error(f"Missing required fields: {', '.join(missing_fields)}")
                return False
            return True

        def find_matching_answer(self, question_text):
            """Find matching answer for a question from answers CSV"""
            logging.info(f"Looking for answer to: {question_text}")

            if not question_text:
                return ""

            # Normalize the question text
            normalized_question = self.normalize_text(question_text)

            # Handle checkbox special cases
            if any(
                keyword in normalized_question.lower()
                for keyword in [
                    "agree",
                    "consent",
                    "acknowledge",
                    "certify",
                    "confirm",
                    "accept",
                    "privacy",
                    "terms",
                ]
            ):
                # For acknowledgements in answers file, check special matches
                for q in self.answers:
                    norm_q = self.normalize_text(q)
                    # Check for related keywords in both question and answer
                    if any(
                        keyword in norm_q
                        for keyword in [
                            "agree",
                            "consent",
                            "acknowledge",
                            "certify",
                            "confirm",
                            "accept",
                            "privacy",
                            "terms",
                        ]
                    ):
                        # If there's any similarity, use this answer
                        common_words = set(normalized_question.split()) & set(
                            norm_q.split()
                        )
                        if common_words and self.answers[q].strip():
                            logging.info(
                                f"Found acknowledgement match for '{question_text}' -> '{q}'"
                            )
                            return self.answers[q]

            # Check for exact matches first
            if normalized_question in self.answers:
                logging.info(f"Found exact match for: {question_text}")
                return self.answers[normalized_question]

            # Check for matches with partial normalization (only lowercase)
            lower_q = question_text.lower()
            for q in self.answers:
                if q.lower() == lower_q:
                    logging.info(f"Found case-insensitive match for: {question_text}")
                    return self.answers[q]

            # Check for partial matches based on fuzzy matching
            best_match = None
            best_score = 0
            for q in self.answers:
                score = fuzz.ratio(q.lower(), lower_q)
                if score > best_score:
                    best_match = q
                    best_score = score

            # If we found a good match (score > 70)
            if best_score > 70 and best_match:
                logging.info(
                    f"Found fuzzy match ({best_score}%) for: {question_text} -> {best_match}"
                )
                return self.answers[best_match]

            # Handle common questions with default answers if not found
            lower_question = normalized_question.lower()

            # Work authorization questions
            if any(
                keyword in lower_question
                for keyword in [
                    "authorized",
                    "authorised",
                    "authorization",
                    "work permit",
                    "legally",
                    "eligible",
                    "sponsor",
                ]
            ):
                if "sponsor" in lower_question:
                    logging.info(
                        f"Using default answer for sponsorship question: {question_text}"
                    )
                    return "No, I do not require sponsorship."
                logging.info(
                    f"Using default answer for work authorization question: {question_text}"
                )
                return "Yes, I am authorized to work in the United States."

            # Salary expectations
            if any(
                keyword in lower_question
                for keyword in ["salary", "compensation", "pay", "range", "expect"]
            ):
                logging.info(
                    f"Using default answer for salary question: {question_text}"
                )
                return "My salary expectations are flexible and negotiable based on the total compensation package."

            # For terms and conditions without an answer
            if any(
                keyword in lower_question
                for keyword in [
                    "privacy policy",
                    "terms",
                    "conditions",
                    "agree",
                    "consent",
                ]
            ):
                # Only return an acknowledgement if we've been specifically told to
                # Check if we have any acknowledgement answer matching this
                for q in self.answers:
                    if any(
                        keyword in q.lower()
                        for keyword in [
                            "privacy policy",
                            "terms",
                            "conditions",
                            "agree",
                            "consent",
                        ]
                    ):
                        norm_q = self.normalize_text(q)
                        common_words = set(normalized_question.split()) & set(
                            norm_q.split()
                        )
                        if common_words and "i acknowledge" in self.answers[q].lower():
                            logging.info(
                                f"Using acknowledge answer for: {question_text}"
                            )
                            return self.answers[q]

                # No matching answer found, don't auto-acknowledge
                logging.warning(f"No answer found for acknowledgement: {question_text}")
                return ""

            logging.warning(f"No answer found for question: {question_text}")
            return ""

        def fill_application_form(self, job_link):
            logging.info(f"Opening job: {job_link}")
            self.driver.get(job_link)
            time.sleep(2)

            if any(
                text in self.driver.page_source
                for text in ["404", "Not Found", "Page not found"]
            ):
                logging.warning("Page not found (404)")
                return "404"

            if "already applied" in self.driver.page_source.lower():
                logging.info("Job already applied to")
                return "already applied"

            if "apply" in self.driver.current_url.lower():
                logging.info("Direct job application form detected")
                return True

            for selector in self.locators["APPLY_SELECTORS"]:
                selector_type = selector.get("type", "css")
                selector_value = selector.get("value", "")
                logging.info(
                    f"Attempting {selector_type} selector for apply button: {selector_value}"
                )
                try:
                    by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                    apply_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by_type, selector_value))
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView();", apply_button
                    )
                    self.driver.execute_script("arguments[0].click();", apply_button)
                    logging.info(
                        f"Clicked 'Apply' button using {selector_type} selector"
                    )
                    time.sleep(3)
                    return True
                except (TimeoutException, NoSuchElementException):
                    logging.warning(
                        f"Failed to click apply button with {selector_type} selector"
                    )
                    continue

            logging.warning("No 'Apply' button found")
            return False

        def handle_location_dropdown(self):
            location_value = self.credentials.get("location")
            if not location_value:
                logging.info(
                    "No location value found in credentials, skipping dropdown"
                )
                return

            try:
                location_dropdown = self.find_element("location_dropdown")
                if not location_dropdown:
                    logging.info("Location dropdown not found, might be optional")
                    return

                logging.info(
                    f"Found location dropdown: {location_dropdown.get_attribute('outerHTML')}"
                )

                # Click to open dropdown
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", location_dropdown
                )
                location_dropdown.click()
                logging.info("Clicked location dropdown")
                time.sleep(1)

                # Try to select from dropdown options
                location_options = self.find_element("location_options", multiple=True)
                if location_options:
                    for option in location_options:
                        option_text = option.text.strip().lower()
                        if self.normalize_text(location_value) in self.normalize_text(
                            option_text
                        ):
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView(true);", option
                            )
                            option.click()
                            logging.info(f"Selected location option: {option_text}")
                            time.sleep(1)
                            return

                    # If no match found, try to type and select the first option
                    location_dropdown.clear()
                    location_dropdown.send_keys(location_value)
                    time.sleep(2)

                    # Try to select first suggestion if any
                    suggestions = self.find_element(
                        "location_suggestions", multiple=True
                    )
                    if suggestions and len(suggestions) > 0:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", suggestions[0]
                        )
                        suggestions[0].click()
                        logging.info(f"Selected first location suggestion")
                        time.sleep(1)
                        return

                # Direct input as fallback
                location_dropdown.clear()
                location_dropdown.send_keys(location_value)
                logging.info(f"Entered location directly: {location_value}")

            except Exception as e:
                logging.warning(f"Error handling location dropdown: {str(e)}")

        def handle_custom_questions(self):
            logging.info("Handling custom questions...")

            # Get all question elements
            question_elements = []

            for selector in self.locators["QUESTION_SELECTORS"]:
                selector_type = selector.get("type", "css")
                selector_value = selector.get("value", "")

                try:
                    by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                    elements = self.driver.find_elements(by_type, selector_value)
                    logging.info(
                        f"Found {len(elements)} questions using {selector_type} selector: {selector_value}"
                    )
                    question_elements.extend(elements)
                except Exception as e:
                    logging.warning(
                        f"Error finding questions with {selector_type} selector: {str(e)}"
                    )

            logging.info(f"Found {len(question_elements)} total custom questions")

            # Special handling for 'Where did you hear' dropdown which is common in Lever
            try:
                hear_about_selectors = [
                    "select[name='source']",
                    "select#source",
                    "select[name*='hear']",
                    "select[id*='hear']",
                ]

                for selector in hear_about_selectors:
                    try:
                        hear_about_select = self.driver.find_element(
                            By.CSS_SELECTOR, selector
                        )
                        logging.info(
                            f"Found 'Where did you hear about this position?' question - special handling"
                        )

                        # Get all options
                        options = [
                            o
                            for o in Select(hear_about_select).options
                            if o.text.strip()
                        ]
                        logging.info(
                            f"Found {len(options)} options for the 'Where did you hear' question"
                        )

                        # Try to select LinkedIn or Job Board if available
                        preferred_options = [
                            "LinkedIn",
                            "Job Board",
                            "Job Posting",
                            "Internet Search",
                        ]

                        for preferred in preferred_options:
                            for option in options:
                                if preferred.lower() in option.text.lower():
                                    Select(hear_about_select).select_by_visible_text(
                                        option.text
                                    )
                                    logging.info(
                                        f"Selected an option for 'Where did you hear' question"
                                    )
                                    break
                            else:
                                continue
                            break
                        else:
                            # If no preferred option found, select the first non-empty option
                            if (
                                options
                                and options[0].text.strip()
                                and options[0].text.lower() != "select"
                            ):
                                Select(hear_about_select).select_by_visible_text(
                                    options[0].text
                                )
                                logging.info(
                                    f"Selected first option for 'Where did you hear' question"
                                )
                    except NoSuchElementException:
                        continue
                    except Exception as e:
                        logging.warning(
                            f"Error handling 'Where did you hear' question: {str(e)}"
                        )
                        continue
            except Exception as e:
                logging.warning(
                    f"Error in special handling for 'Where did you hear' question: {str(e)}"
                )

            # Process each question element
            for question_element in question_elements:
                try:
                    # Extract question text
                    question_text = ""
                    label = None

                    # Try to find label
                    for selector in self.locators["QUESTION_FIELD_SELECTORS"]["label"]:
                        selector_type = selector.get("type", "css")
                        selector_value = selector.get("value", "")

                        try:
                            by_type = (
                                By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                            )
                            label = question_element.find_element(
                                by_type, selector_value
                            )
                            question_text = label.text.strip()
                            logging.info(
                                f"Found question text from label: {question_text}"
                            )
                            break
                        except NoSuchElementException:
                            continue

                    # If no label found, use the text from the question element
                    if not question_text:
                        question_text = question_element.text.strip()
                        logging.info(
                            f"Extracted question text from container: {question_text}"
                        )

                    # Skip if the question is about 'Where did you hear' (handled separately)
                    if "hear about" in question_text.lower():
                        logging.info(
                            f"Skipping 'Where did you hear' question as it was handled separately"
                        )
                        continue

                    # Skip resume/CV questions (handled separately)
                    if any(
                        keyword in question_text.lower()
                        for keyword in ["resume", "cv", "upload"]
                    ):
                        logging.info(f"Skipping resume question: {question_text}")
                        continue

                    # Find the answer for this question
                    answer = self.find_matching_answer(question_text)
                    if not answer:
                        logging.warning(
                            f"Could not find input field for question: {question_text}"
                        )
                        continue

                    # Try filling in the answer using various input types
                    input_filled = False

                    # Try textarea
                    if not input_filled:
                        for selector in self.locators["QUESTION_FIELD_SELECTORS"][
                            "textarea"
                        ]:
                            selector_type = selector.get("type", "css")
                            selector_value = selector.get("value", "")

                            try:
                                by_type = (
                                    By.CSS_SELECTOR
                                    if selector_type == "css"
                                    else By.XPATH
                                )
                                textarea = question_element.find_element(
                                    by_type, selector_value
                                )
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'center'});",
                                    textarea,
                                )
                                textarea.clear()
                                textarea.send_keys(answer)
                                logging.info(
                                    f"Filled textarea for question '{question_text}' with answer '{answer}'"
                                )
                                input_filled = True
                                break
                            except Exception:
                                continue

                    # Try text input
                    if not input_filled:
                        for selector in self.locators["QUESTION_FIELD_SELECTORS"][
                            "text_input"
                        ]:
                            selector_type = selector.get("type", "css")
                            selector_value = selector.get("value", "")

                            try:
                                by_type = (
                                    By.CSS_SELECTOR
                                    if selector_type == "css"
                                    else By.XPATH
                                )
                                text_input = question_element.find_element(
                                    by_type, selector_value
                                )
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'center'});",
                                    text_input,
                                )
                                text_input.clear()
                                text_input.send_keys(answer)
                                logging.info(
                                    f"Filled text input for question '{question_text}' with answer '{answer}'"
                                )
                                input_filled = True
                                break
                            except Exception:
                                continue

                    # Try dropdown
                    if not input_filled:
                        for selector in self.locators["QUESTION_FIELD_SELECTORS"][
                            "dropdown"
                        ]:
                            selector_type = selector.get("type", "css")
                            selector_value = selector.get("value", "")

                            try:
                                by_type = (
                                    By.CSS_SELECTOR
                                    if selector_type == "css"
                                    else By.XPATH
                                )
                                dropdown = question_element.find_element(
                                    by_type, selector_value
                                )
                                select = Select(dropdown)

                                try:
                                    # Try exact match first
                                    select.select_by_visible_text(answer)
                                    logging.info(
                                        f"Selected dropdown option '{answer}' for question '{question_text}'"
                                    )
                                    input_filled = True
                                    break
                                except Exception:
                                    # Try to find partial match
                                    options = [
                                        option.text.strip() for option in select.options
                                    ]
                                    for option in options:
                                        if self.normalize_text(
                                            answer
                                        ) in self.normalize_text(
                                            option
                                        ) or self.normalize_text(
                                            option
                                        ) in self.normalize_text(
                                            answer
                                        ):
                                            select.select_by_visible_text(option)
                                            logging.info(
                                                f"Selected best matching option '{option}' for question '{question_text}'"
                                            )
                                            input_filled = True
                                            break

                                    if not input_filled and len(select.options) > 1:
                                        # Select first non-empty option that's not "Select"
                                        for option in select.options:
                                            if (
                                                option.text.strip()
                                                and option.text.lower() != "select"
                                                and not option.get_attribute("disabled")
                                            ):
                                                select.select_by_visible_text(
                                                    option.text
                                                )
                                                logging.info(
                                                    f"Selected first non-empty option '{option.text}' for question '{question_text}'"
                                                )
                                                input_filled = True
                                                break
                            except Exception:
                                continue

                    # Try radio buttons
                    if not input_filled:
                        for selector in self.locators["QUESTION_FIELD_SELECTORS"][
                            "radio_button"
                        ]:
                            selector_type = selector.get("type", "css")
                            selector_value = selector.get("value", "")

                            try:
                                by_type = (
                                    By.CSS_SELECTOR
                                    if selector_type == "css"
                                    else By.XPATH
                                )
                                radios = question_element.find_elements(
                                    by_type, selector_value
                                )

                                if radios:
                                    # Try to find radio button that matches the answer
                                    for radio in radios:
                                        if self.normalize_text(
                                            radio.get_attribute("value") or ""
                                        ) == self.normalize_text(
                                            answer
                                        ) or self.normalize_text(
                                            radio.get_attribute("id") or ""
                                        ) == self.normalize_text(
                                            answer
                                        ):
                                            self.driver.execute_script(
                                                "arguments[0].scrollIntoView({block: 'center'});",
                                                radio,
                                            )
                                            self.driver.execute_script(
                                                "arguments[0].click();", radio
                                            )
                                            logging.info(
                                                f"Selected radio button for question '{question_text}' with value matching '{answer}'"
                                            )
                                            input_filled = True
                                            break

                                    # If no match found, and answer is Yes/No, try to match that
                                    if not input_filled and answer.lower() in [
                                        "yes",
                                        "no",
                                    ]:
                                        for radio in radios:
                                            label_text = ""
                                            try:
                                                # Try to get the label text
                                                radio_id = radio.get_attribute("id")
                                                if radio_id:
                                                    label_element = (
                                                        self.driver.find_element(
                                                            By.CSS_SELECTOR,
                                                            f"label[for='{radio_id}']",
                                                        )
                                                    )
                                                    label_text = (
                                                        label_element.text.strip()
                                                    )
                                                else:
                                                    parent = radio.find_element(
                                                        By.XPATH, "./.."
                                                    )
                                                    label_text = parent.text.strip()
                                            except Exception:
                                                pass

                                            if self.normalize_text(
                                                label_text
                                            ) == self.normalize_text(answer):
                                                self.driver.execute_script(
                                                    "arguments[0].scrollIntoView({block: 'center'});",
                                                    radio,
                                                )
                                                self.driver.execute_script(
                                                    "arguments[0].click();", radio
                                                )
                                                logging.info(
                                                    f"Selected radio button with label '{label_text}' for question '{question_text}'"
                                                )
                                                input_filled = True
                                                break

                                    # If still no match, select the first radio button for required fields
                                    if not input_filled and any(
                                        indicator in question_text
                                        for indicator in self.locators[
                                            "QUESTION_FIELD_SELECTORS"
                                        ]["required_indicator"]
                                    ):
                                        self.driver.execute_script(
                                            "arguments[0].scrollIntoView({block: 'center'});",
                                            radios[0],
                                        )
                                        self.driver.execute_script(
                                            "arguments[0].click();", radios[0]
                                        )
                                        logging.info(
                                            f"Selected first radio button for required question '{question_text}'"
                                        )
                                        input_filled = True
                            except Exception:
                                continue

                    # Try checkboxes
                    if not input_filled:
                        for selector in self.locators["QUESTION_FIELD_SELECTORS"][
                            "checkbox"
                        ]:
                            selector_type = selector.get("type", "css")
                            selector_value = selector.get("value", "")

                            try:
                                by_type = (
                                    By.CSS_SELECTOR
                                    if selector_type == "css"
                                    else By.XPATH
                                )
                                checkboxes = question_element.find_elements(
                                    by_type, selector_value
                                )

                                if checkboxes:
                                    # If this is an acknowledgement/agreement checkbox
                                    if any(
                                        keyword in question_text.lower()
                                        for keyword in [
                                            "agree",
                                            "acknowledge",
                                            "certify",
                                            "confirm",
                                        ]
                                    ):
                                        if not checkboxes[0].is_selected():
                                            self.driver.execute_script(
                                                "arguments[0].scrollIntoView({block: 'center'});",
                                                checkboxes[0],
                                            )
                                            self.driver.execute_script(
                                                "arguments[0].click();", checkboxes[0]
                                            )
                                            logging.info(
                                                f"Checked acknowledgement checkbox for question '{question_text}'"
                                            )
                                            input_filled = True

                                    # If this is a required checkbox
                                    elif any(
                                        indicator in question_text
                                        for indicator in self.locators[
                                            "QUESTION_FIELD_SELECTORS"
                                        ]["required_indicator"]
                                    ):
                                        if not checkboxes[0].is_selected():
                                            self.driver.execute_script(
                                                "arguments[0].scrollIntoView({block: 'center'});",
                                                checkboxes[0],
                                            )
                                            self.driver.execute_script(
                                                "arguments[0].click();", checkboxes[0]
                                            )
                                            logging.info(
                                                f"Checked required checkbox for question '{question_text}'"
                                            )
                                            input_filled = True
                            except Exception:
                                continue

                    if not input_filled:
                        logging.warning(
                            f"Could not find input field for question: {question_text}"
                        )

                except Exception as e:
                    logging.warning(f"Error processing question: {str(e)}")
                    continue

        def handle_acknowledgements(self):
            logging.info("Handling acknowledgements and agreements...")

            # Try to find all acknowledgement checkboxes
            checkbox_selectors = []

            # Get all checkboxes from the acknowledgement selectors
            for selector in self.locators["ACKNOWLEDGEMENT_SELECTORS"]:
                selector_type = selector.get("type", "css")
                selector_value = selector.get("value", "")

                checkbox_selectors.append((selector_type, selector_value))

            # Also check for required checkboxes
            checkbox_selectors.append(("css", "input[type='checkbox'][required]"))

            for selector_type, selector_value in checkbox_selectors:
                try:
                    by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                    checkboxes = self.driver.find_elements(by_type, selector_value)
                    if checkboxes:
                        logging.info(
                            f"Found {len(checkboxes)} acknowledgement checkboxes using {selector_type} selector: {selector_value}"
                        )

                        # Process each checkbox individually
                        for checkbox in checkboxes:
                            try:
                                # Try to get the text associated with this checkbox
                                checkbox_text = ""

                                # Try to find associated label by for attribute
                                checkbox_id = checkbox.get_attribute("id")
                                if checkbox_id:
                                    try:
                                        label = self.driver.find_element(
                                            By.CSS_SELECTOR,
                                            f"label[for='{checkbox_id}']",
                                        )
                                        checkbox_text = label.text.strip()
                                    except NoSuchElementException:
                                        pass

                                # If no label found, try parent element's text
                                if not checkbox_text:
                                    try:
                                        parent = checkbox.find_element(
                                            By.XPATH, "./parent::*"
                                        )
                                        checkbox_text = parent.text.strip()
                                    except:
                                        pass

                                # If still no text, try to find associated text in nearby elements
                                if not checkbox_text:
                                    try:
                                        nearby_text = checkbox.find_element(
                                            By.XPATH, "./following-sibling::*[1]"
                                        )
                                        checkbox_text = nearby_text.text.strip()
                                    except:
                                        pass

                                # If still no text, use the name or value attribute
                                if not checkbox_text:
                                    checkbox_text = (
                                        checkbox.get_attribute("name")
                                        or checkbox.get_attribute("value")
                                        or ""
                                    )

                                # Log the checkbox text for debugging
                                if checkbox_text:
                                    logging.info(
                                        f"Found checkbox with text: {checkbox_text}"
                                    )
                                else:
                                    logging.info(
                                        "Found checkbox without associated text"
                                    )

                                # Check if we should check this checkbox based on our answers
                                should_check = False

                                # Check if this is an acknowledgement checkbox based on text content
                                keywords = [
                                    "agree",
                                    "consent",
                                    "acknowledge",
                                    "certify",
                                    "accept",
                                    "confirm",
                                    "privacy",
                                    "terms",
                                    "conditions",
                                ]

                                if checkbox_text:
                                    # First check for exact match in answers
                                    answer = self.find_matching_answer(checkbox_text)
                                    if answer and answer.lower() in [
                                        "yes",
                                        "true",
                                        "i agree",
                                        "i acknowledge",
                                        "i accept",
                                        "i consent",
                                        "i confirm",
                                        "agree",
                                        "accept",
                                        "1",
                                    ]:
                                        should_check = True
                                        logging.info(
                                            f"Found answer '{answer}' for checkbox text '{checkbox_text}'"
                                        )

                                    # If it's a common acknowledgement type, only check if we have a matching answer with affirmative response
                                    elif any(
                                        keyword in checkbox_text.lower()
                                        for keyword in keywords
                                    ):
                                        # Only check common acknowledgements if we have an answer for it
                                        answer = self.find_matching_answer(
                                            checkbox_text
                                        )
                                        if answer and answer.lower() in [
                                            "yes",
                                            "true",
                                            "i agree",
                                            "i acknowledge",
                                            "i accept",
                                            "i consent",
                                            "i confirm",
                                            "agree",
                                            "accept",
                                            "1",
                                        ]:
                                            should_check = True
                                            logging.info(
                                                f"Found acknowledgement checkbox with answer '{answer}'"
                                            )

                                # Check if this checkbox is marked as required (always check these)
                                is_required = (
                                    checkbox.get_attribute("required") is not None
                                    or checkbox.get_attribute("aria-required") == "true"
                                )

                                # For required checkboxes, be more selective
                                if is_required:
                                    # Get surrounding context to determine if this is an acknowledgement-type checkbox
                                    if checkbox_text:
                                        # Only check required checkboxes if they appear to be acknowledgements or if we have an answer
                                        keywords = [
                                            "agree",
                                            "consent",
                                            "acknowledge",
                                            "certify",
                                            "accept",
                                            "confirm",
                                            "privacy",
                                            "terms",
                                            "conditions",
                                        ]
                                        if any(
                                            keyword in checkbox_text.lower()
                                            for keyword in keywords
                                        ):
                                            # Look for an answer that matches this checkbox
                                            answer = self.find_matching_answer(
                                                checkbox_text
                                            )
                                            if answer and answer.lower() in [
                                                "yes",
                                                "true",
                                                "i agree",
                                                "i acknowledge",
                                                "i accept",
                                                "i consent",
                                                "i confirm",
                                                "agree",
                                                "accept",
                                                "1",
                                            ]:
                                                should_check = True
                                                logging.info(
                                                    f"Found required acknowledgement with matching answer: {checkbox_text}"
                                                )
                                            else:
                                                # Only automatically check essential agreement checkboxes when required
                                                # Check if this is a critical agreement (privacy policy, terms of service)
                                                critical_keywords = [
                                                    "privacy policy",
                                                    "terms of service",
                                                    "terms and conditions",
                                                ]
                                                if any(
                                                    keyword in checkbox_text.lower()
                                                    for keyword in critical_keywords
                                                ):
                                                    should_check = True
                                                    logging.info(
                                                        f"Checking critical agreement checkbox (required): {checkbox_text}"
                                                    )
                                                else:
                                                    logging.info(
                                                        f"Skipping non-critical required checkbox without answer: {checkbox_text}"
                                                    )
                                        else:
                                            logging.info(
                                                f"Skipping required checkbox (not an acknowledgement): {checkbox_text}"
                                            )
                                    else:
                                        # Without text, we can't determine if this is an acknowledgement checkbox
                                        # Default to not checking it unless it's clearly required for submission
                                        logging.info(
                                            "Found required checkbox without text - skipping as we can't determine purpose"
                                        )
                                        should_check = False

                                # If the checkbox should be checked and is not already selected
                                if should_check and not checkbox.is_selected():
                                    self.driver.execute_script(
                                        "arguments[0].scrollIntoView({block: 'center'});",
                                        checkbox,
                                    )
                                    time.sleep(0.5)
                                    self.driver.execute_script(
                                        "arguments[0].click();", checkbox
                                    )
                                    logging.info(
                                        f"Checked checkbox: {checkbox_text if checkbox_text else 'unnamed checkbox'}"
                                    )
                                    time.sleep(1)  # Shorter wait between clicks
                                elif not should_check:
                                    logging.info(
                                        f"Skipping checkbox: {checkbox_text if checkbox_text else 'unnamed checkbox'}"
                                    )

                            except Exception as e:
                                logging.warning(f"Error processing checkbox: {str(e)}")
                except Exception as e:
                    logging.warning(
                        f"Error finding checkboxes with {selector_type} selector: {str(e)}"
                    )
                    continue

        def submit_application(self):
            logging.info("Attempting to submit application...")

            # Find a submit button using the selectors
            for selector in self.locators["SUBMIT_SELECTORS"]:
                selector_type = selector.get("type", "css")
                selector_value = selector.get("value", "")

                try:
                    by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                    submit_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((by_type, selector_value))
                    )

                    # Log the found button for debugging
                    logging.info(
                        f"Found submit button using {selector_type} selector: {selector_value}"
                    )

                    # Scroll to the button and click it
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", submit_button
                    )
                    time.sleep(1)  # Wait for any animations to complete

                    # Use JavaScript click to ensure it works
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    logging.info("Clicked submit button")

                    # Wait a moment for the submission to process
                    time.sleep(3)
                    return True
                except Exception as e:
                    logging.warning(
                        f"Error clicking submit button with {selector_type} selector {selector_value}: {str(e)}"
                    )
                    continue

            logging.warning(
                "No submit button found or could not click any submit button"
            )
            return False

        def verify_submission(self):
            logging.info("Verifying submission status...")

            try:
                # Wait for potential success messages
                success_indicators = [
                    # URLs that indicate success
                    lambda: any(
                        keyword in self.driver.current_url.lower()
                        for keyword in ["thank", "success", "done", "confirmation"]
                    ),
                    # Success messages with text checking
                    lambda: any(
                        text in self.driver.page_source.lower()
                        for text in [
                            "thank you for applying",
                            "application submitted",
                            "application has been submitted",
                            "application complete",
                            "successfully submitted",
                            "thank you for your interest",
                            "we have received your application",
                        ]
                    ),
                    # Check for elements that appear on success pages
                    lambda: len(
                        self.driver.find_elements(
                            By.CSS_SELECTOR,
                            ".success-message, .thank-you-message, .confirmation-message",
                        )
                    )
                    > 0,
                ]

                # Wait a bit for any redirects or page changes to complete
                time.sleep(3)

                # Check all success indicators
                for indicator in success_indicators:
                    try:
                        if indicator():
                            logging.info("Application submitted successfully")
                            return True
                    except Exception:
                        continue

                # Check for error messages
                error_indicators = [
                    # Error messages commonly found when submission fails
                    lambda: any(
                        text in self.driver.page_source.lower()
                        for text in [
                            "error",
                            "invalid",
                            "failed",
                            "missing required",
                            "please fill",
                        ]
                    )
                ]

                for indicator in error_indicators:
                    try:
                        if indicator():
                            error_text = next(
                                (
                                    text
                                    for text in [
                                        "error",
                                        "invalid",
                                        "failed",
                                        "missing required",
                                        "please fill",
                                    ]
                                    if text in self.driver.page_source.lower()
                                ),
                                "unknown error",
                            )
                            logging.warning(
                                f"Submission failed, found error message: '{error_text}'"
                            )
                            return False
                    except Exception:
                        continue

                # If we can't determine either way, assume it didn't work
                logging.warning("Could not verify submission status, assuming failure")
                return False

            except Exception as e:
                logging.warning(f"Error verifying submission: {str(e)}")
                return False

        def fill_basic_fields(self):
            self.upload_resume()

            filled_fields = set()

            for field_key, selectors in self.locators["FIELD_SELECTORS"].items():
                if field_key in [
                    "resume",
                    "resume_path",
                    "resume_upload_button",
                    "resume_upload_confirmation",
                ]:
                    continue
                if field_key not in self.credentials or field_key in filled_fields:
                    continue

                value = self.credentials[field_key]
                if not value:
                    logging.warning(f"No value for {field_key} in credentials")
                    continue

                selectors = selectors if isinstance(selectors, list) else [selectors]
                logging.info(f"Attempting to fill {field_key} with: {value}")

                for selector in selectors:
                    selector_type = selector.get("type", "css")
                    selector_value = selector.get("value", "")
                    try:
                        by_type = (
                            By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                        )
                        input_field = WebDriverWait(self.driver, 10).until(
                            EC.visibility_of_element_located((by_type, selector_value))
                        )
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", input_field
                        )
                        input_field.clear()
                        input_field.send_keys(value)
                        logging.info(f"Filled {field_key}: {value}")
                        filled_fields.add(field_key)
                        break
                    except (
                        TimeoutException,
                        NoSuchElementException,
                        ElementNotInteractableException,
                    ) as e:
                        logging.warning(
                            f"Failed to fill {field_key} with {selector_type} selector {selector_value}: {str(e)}"
                        )
                        continue

        def open_job_and_click_apply(self, job_link):
            logging.info(f"Opening job: {job_link}")
            self.driver.get(job_link)
            time.sleep(2)

            if any(
                text in self.driver.page_source
                for text in ["404", "Not Found", "Page not found"]
            ):
                logging.warning("Page not found (404)")
                return "404"

            if "already applied" in self.driver.page_source.lower():
                logging.info("Job already applied to")
                return "already applied"

            if "apply" in self.driver.current_url.lower():
                logging.info("Direct job application form detected")
                return True

            for selector in self.locators["APPLY_SELECTORS"]:
                selector_type = selector.get("type", "css")
                selector_value = selector.get("value", "")
                logging.info(
                    f"Attempting {selector_type} selector for apply button: {selector_value}"
                )
                try:
                    by_type = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
                    apply_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by_type, selector_value))
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView();", apply_button
                    )
                    self.driver.execute_script("arguments[0].click();", apply_button)
                    logging.info(
                        f"Clicked 'Apply' button using {selector_type} selector"
                    )
                    time.sleep(3)
                    return True
                except (TimeoutException, NoSuchElementException):
                    logging.warning(
                        f"Failed to click apply button with {selector_type} selector"
                    )
                    continue

            logging.warning("No 'Apply' button found")
            return False

        def save_session_state(self, job_link):
            session_data = {
                "current_url": self.driver.current_url,
                "cookies": self.driver.get_cookies(),
                "timestamp": datetime.now().isoformat(),
            }
            with open(f"session_{job_link.split('/')[-1]}.json", "w") as f:
                json.dump(session_data, f)

        def load_session_state(self, job_link):
            try:
                with open(f"session_{job_link.split('/')[-1]}.json", "r") as f:
                    session_data = json.load(f)
                    self.driver.get(session_data["current_url"])
                    for cookie in session_data["cookies"]:
                        self.driver.add_cookie(cookie)
                    self.driver.refresh()
                    return True
            except FileNotFoundError:
                return False

        def load_locators(self):
            try:
                with open("locators/lever_locators.json", "r") as f:
                    self.locators = json.load(f)
            except FileNotFoundError:
                logging.error("Locators file not found.")
                raise
            except json.JSONDecodeError:
                logging.error("Invalid JSON in locators file.")
                raise

        def load_answers(self, file_path):
            """Load answers from a CSV file into a dictionary"""
            answers = {}
            try:
                with open(file_path, mode="r", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        question = row["Question"].strip().lower()
                        answers[question] = row["Answer"].strip()
                return answers
            except FileNotFoundError:
                logging.error(f"Answers file '{file_path}' not found.")
                raise

        def setup_driver(self):
            """Set up and return a Chrome WebDriver instance with optimal settings"""
            chrome_options = uc.ChromeOptions()

            # Anti-detection measures
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Add user agent to appear more like a regular browser
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
            )

            # Avoid SSL certificate issues
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--allow-running-insecure-content")

            try:
                # Use undetected_chromedriver to avoid bot detection
                driver = uc.Chrome(options=chrome_options)

                # Set page load timeout to 30 seconds
                driver.set_page_load_timeout(30)

                return driver
            except Exception as e:
                logging.error(f"Failed to initialize Chrome driver: {str(e)}")

                # Fallback to regular ChromeDriver if undetected_chromedriver fails
                try:
                    from selenium import webdriver

                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver.set_page_load_timeout(30)
                    logging.warning("Using regular ChromeDriver as fallback")
                    return driver
                except Exception as e2:
                    logging.error(
                        f"Fallback driver initialization also failed: {str(e2)}"
                    )
                    raise

        def log_application_status(self, job_link, status):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file = f"logs/job_application_{self.candidate_name}_{datetime.now().strftime('%Y-%m-%d')}.csv"

            try:
                os.makedirs("logs", exist_ok=True)
                file_exists = os.path.isfile(log_file)

                with open(log_file, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                    if not file_exists:
                        writer.writerow(["jobLink", "timestamp", "status"])
                    writer.writerow([job_link, timestamp, status])
                    f.flush()
                logging.info(f'Logged to CSV: "{job_link}","{timestamp}","{status}"')
            except Exception as e:
                logging.error(f"Failed to log to {log_file}: {e}")

        def process_job_application(self, job_link, max_retries=2):
            for attempt in range(max_retries + 1):
                try:
                    result = self.open_job_and_click_apply(job_link)
                    if result == "404":
                        return "failed - 404 not found"
                    elif result == "already applied":
                        return "already applied"
                    elif not result:
                        return "failed - could not apply"

                    if not self.validate_required_fields():
                        return "failed - missing required fields"

                    self.fill_basic_fields()
                    self.handle_location_dropdown()
                    self.handle_custom_questions()
                    self.handle_acknowledgements()

                    # Check if there are any required checkboxes that are still unchecked
                    unchecked_required = []
                    try:
                        required_checkboxes = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            "input[type='checkbox'][required]:not(:checked)",
                        )
                        if required_checkboxes:
                            for checkbox in required_checkboxes:
                                # Try to get the text for this checkbox
                                checkbox_text = ""
                                try:
                                    # Try to find associated label by for attribute
                                    checkbox_id = checkbox.get_attribute("id")
                                    if checkbox_id:
                                        label = self.driver.find_element(
                                            By.CSS_SELECTOR,
                                            f"label[for='{checkbox_id}']",
                                        )
                                        checkbox_text = label.text.strip()
                                except:
                                    pass

                                if not checkbox_text:
                                    try:
                                        parent = checkbox.find_element(
                                            By.XPATH, "./parent::*"
                                        )
                                        checkbox_text = parent.text.strip()
                                    except:
                                        checkbox_text = "Unknown checkbox"

                                unchecked_required.append(checkbox_text)

                        if unchecked_required:
                            logging.warning(
                                f"There are {len(unchecked_required)} required checkboxes still unchecked:"
                            )
                            for text in unchecked_required:
                                logging.warning(f"  - {text}")
                            logging.warning(
                                "You may need to manually check these before submission"
                            )
                    except Exception as e:
                        logging.warning(
                            f"Error checking for unchecked required checkboxes: {str(e)}"
                        )

                    logging.info("Pausing for 10sec for manual review...")
                    time.sleep(10)

                    if self.submit_application():
                        if self.verify_submission():
                            return "success"
                        return "failed - submission verification failed"
                    return "failed - submission failed"

                except Exception as e:  # Catch all exceptions
                    logging.error(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries:
                        time.sleep(5)
                        self.driver.quit()
                        self.driver = self.setup_driver()
                    else:
                        return f"failed - max retries exceeded: {str(e)}"

        def run(self, job_links_file="jobs/linkedin_jobs.csv"):
            if not os.path.exists(job_links_file):
                logging.error(f"CSV file '{job_links_file}' not found.")
                return

            job_links_df = pd.read_csv(job_links_file)
            required_columns = ["company", "platform", "job_id", "platform_link"]

            if not all(col in job_links_df.columns for col in required_columns):
                logging.error("Missing required columns in CSV file.")
                return

            job_links = []
            for row in job_links_df.itertuples(index=False):
                if str(row.platform).lower() == "lever":
                    job_links.append(
                        f"{self.lever_base_url}/{row.company}/{row.job_id}"
                    )

            if not job_links:
                logging.error("No Lever job links found in the CSV file.")
                return

            for job_link in job_links:
                logging.info(f"Processing job: {job_link}")

                if self.load_session_state(job_link):
                    logging.info("Resuming interrupted application")
                else:
                    logging.info("Starting new application")

                try:
                    status = self.process_job_application(job_link)
                    self.log_application_status(job_link, status)

                    if status == "success":
                        logging.info("Application successful!")
                        if os.path.exists(f"session_{job_link.split('/')[-1]}.json"):
                            os.remove(f"session_{job_link.split('/')[-1]}.json")
                    elif status == "already applied":
                        logging.info("Already applied to this position")
                    else:
                        logging.warning(f"Application failed: {status}")

                except KeyboardInterrupt:
                    logging.info("Application interrupted - saving state")
                    self.save_session_state(job_link)
                    return
                except Exception as e:
                    logging.error(f"Unexpected error: {str(e)}")
                    self.log_application_status(job_link, f"failed - {str(e)}")
                    continue

            self.driver.quit()
            logging.info("Job application process completed!")

    automation = LeverAutomation()
    automation.run()


def main():
    applications = ["greenhouse", "jobvite", "lever"]
    print("Select the application to run:")
    for i, app in enumerate(applications, start=1):
        print(f"{i}. {app}")

    choice = int(input("Enter the number of your choice: ")) - 1

    if choice < 0 or choice >= len(applications):
        logging.error("Invalid choice.")
        sys.exit(1)

    app_name = applications[choice]

    # Get user configuration only once
    config_files = list_user_configs()
    selected_config = select_user_config(config_files)
    username = selected_config.replace(".yaml", "")
    credentials = load_credentials(selected_config)

    # Load platform-specific configurations
    config = load_config(app_name)
    locators = load_locators(app_name)
    jobs = load_jobs()
    resume = load_resume(app_name, username)
    setup_logging(app_name)

    if app_name == "greenhouse":
        run_greenhouse(config, locators, credentials, jobs, resume)
    elif app_name == "jobvite":
        run_jobvite(config, locators, credentials, jobs, resume)
    elif app_name == "lever":
        run_lever(config, locators, credentials, jobs, resume)


if __name__ == "__main__":
    main()
