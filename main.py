import re
import os
import glob
import time
import random
import csv
import yaml
import json
import datetime
import logging
import pandas as pd
import subprocess
import sys
from fuzzywuzzy import fuzz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

def setup_driver():
    """Setup and return a configured WebDriver."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_version = None
        try:
            if sys.platform == "darwin":  # macOS
                chrome_version = (
                    subprocess.check_output(
                        [
                            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                            "--version",
                        ]
                    )
                    .decode("utf-8")
                    .strip()
                    .split()[-1]
                )
            elif sys.platform == "win32":  # Windows
                chrome_version = (
                    subprocess.check_output(
                        [
                            "reg",
                            "query",
                            "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon",
                            "/v",
                            "version",
                        ]
                    )
                    .decode("utf-8")
                    .strip()
                    .split()[-1]
                )
            elif sys.platform == "linux":  # Linux
                chrome_version = (
                    subprocess.check_output(["google-chrome", "--version"])
                    .decode("utf-8")
                    .strip()
                    .split()[-1]
                )
        except Exception as e:
            logging.warning(f"Could not determine Chrome version: {e}")

        if chrome_version:
            logging.info(f"Detected Chrome version: {chrome_version}")
            service = Service(ChromeDriverManager().install())
        else:
            service = Service(ChromeDriverManager().install())

        driver = uc.Chrome(
            options=chrome_options,
            service=service,
            version_main=int(chrome_version.split('.')[0]) if chrome_version else None
        )
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {e}")
        raise
# class GreenhouseAutomation:
#     def __init__(self):
#         self.setup_logging()

#     def setup_logging(self):
#         if not os.path.exists("logs"):
#             os.makedirs("logs")
#         logging.basicConfig(
#             filename="logs/greenhouse_terminal.log",
#             level=logging.INFO,
#             format="%(asctime)s - %(levelname)s - %(message)s"
#         )
#         console_handler = logging.StreamHandler(sys.stdout)
#         console_handler.setLevel(logging.INFO)
#         formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
#         console_handler.setFormatter(formatter)
#         logging.getLogger().addHandler(console_handler)

#     def list_users(self, credentials_dir="credentials"):
#         yaml_files = glob.glob(os.path.join(credentials_dir, "*.yaml"))
#         users = [os.path.splitext(os.path.basename(file))[0] for file in yaml_files]
#         return users

#     def load_user_credentials(self, username, credentials_dir="credentials"):
#         credentials_file = os.path.join(credentials_dir, f"{username}.yaml")
#         return self.load_credentials(credentials_file)

#     def load_user_resume(self, username, resume_dir="resume"):
#         resume_file = os.path.join(resume_dir, f"{username}.pdf")
#         if not os.path.exists(resume_file):
#             logging.error(f"Error: Resume file '{resume_file}' not found for user '{username}'.")
#             return None
#         return os.path.abspath(resume_file)

#     def load_credentials(self, filename):
#         if not os.path.exists(filename):
#             logging.error(f"Error: credentials file '{filename}' not found!")
#             return None
#         with open(filename, "r", encoding="utf-8") as file:
#             credentials = yaml.safe_load(file)
#             base_dir = os.path.dirname(os.path.abspath(__file__))
#             credentials["resume"] = os.path.abspath(os.path.join(base_dir, credentials["resume"]))
#             return credentials

#     def load_job_urls(self, filename="jobs/linkedin_jobs.csv"):
#         job_urls = []
#         if not os.path.exists(filename):
#             logging.error(f"Error: The file '{filename}' was not found.")
#             return []
#         with open(filename, "r", encoding="utf-8") as file:
#             reader = csv.DictReader(file)
#             for row in reader:
#                 platform = row["platform"].strip().lower()
#                 company = row["company"].strip().replace(" ", "").lower()
#                 job_id = row["job_id"].strip()
#                 platform_link = row["platform_link"].strip()
#                 if platform != "greenhouse":
#                     continue
#                 job_url = None
#                 if company and job_id:
#                     job_url = f"https://boards.greenhouse.io/{company}/jobs/{job_id}"
#                 elif platform_link:
#                     job_url = platform_link
#                 if job_url:
#                     job_urls.append(job_url)
#                 else:
#                     logging.warning(f"Skipping job with missing data: {row}")
#         return job_urls

#     def normalize_text(self, text):
#         return text.strip().lower().replace("*", "").replace(".", "").replace(" ", "")

#     def load_qa_pairs(self, filename="config/greenhouse_answers.csv"):
#         qa_pairs = {}
#         if not os.path.exists(filename):
#             logging.error(f"Error: The file '{filename}' was not found.")
#             return qa_pairs
#         with open(filename, "r", encoding="utf-8") as file:
#             reader = csv.reader(file)
#             next(reader, None)
#             for row in reader:
#                 if len(row) >= 2:
#                     question = row[0].strip()
#                     answer = row[1].strip()
#                     qa_pairs[self.normalize_text(question)] = answer
#         return qa_pairs

#     def load_locators(self, filename="locators/greenhouse_locators.json"):
#         if not os.path.exists(filename):
#             logging.error(f"Error: Locators file '{filename}' not found!")
#             return {}
#         with open(filename, "r", encoding="utf-8") as file:
#             return json.load(file)

#     def random_sleep(self, min_time=2, max_time=8):
#         sleep_time = random.uniform(min_time, max_time)
#         logging.info(f"Sleeping for {round(sleep_time, 2)} seconds.")
#         time.sleep(sleep_time)

#     def log_result_to_csv(self, filename, url, status):
#         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         with open(filename, mode="a", newline="", encoding="utf-8") as file:
#             writer = csv.writer(file)
#             writer.writerow([url, status, timestamp])

#     def initialize_csv(self, filename):
#         with open(filename, mode="w", newline="", encoding="utf-8") as file:
#             writer = csv.writer(file)
#             writer.writerow(["URL", "Status", "Timestamp"])

#     def apply_greenhouse(self, driver, url, qa_pairs, locators, user_config):
#         logging.info(f"Applying to: {url}")
#         driver.get(url)
#         self.random_sleep()

#         try:
#             apply_button_selectors = locators.get("apply_buttons", [])
#             apply_button_clicked = False
#             for selector in apply_button_selectors:
#                 try:
#                     apply_button = driver.find_element(By.XPATH, selector)
#                     driver.execute_script("arguments[0].scrollIntoView();", apply_button)
#                     apply_button.click()
#                     logging.info(f"'Apply' button clicked using selector: {selector}")
#                     apply_button_clicked = True
#                     break
#                 except (NoSuchElementException, ElementNotInteractableException):
#                     continue
#             if not apply_button_clicked:
#                 logging.info("No 'Apply' button found. Proceeding with form filling.")
#             self.random_sleep()

#             fields = locators.get("fields", {})
#             for key, field_id in fields.items():
#                 try:
#                     field = driver.find_element(By.ID, field_id)
#                     field.clear()
#                     field.send_keys(user_config[key])
#                     logging.info(f"{key} filled.")
#                 except NoSuchElementException:
#                     logging.info(f"{key} field not found. It might be optional.")

#             self.random_sleep()

#             try:
#                 location_input = driver.find_element(
#                     By.ID, locators.get("location_input", "")
#                 )
#                 location_input.clear()
#                 location_input.send_keys(user_config["location"])
#                 time.sleep(2)
#                 location_input.send_keys(Keys.ARROW_DOWN)
#                 location_input.send_keys(Keys.RETURN)
#                 logging.info(f"Location set to {user_config['location']} (dropdown selected)")
#             except NoSuchElementException:
#                 logging.info("Location input field not found. Skipping.")

#             self.random_sleep()

#             try:
#                 resume_input = driver.find_element(
#                     By.CSS_SELECTOR, locators.get("resume_input", "")
#                 )
#                 driver.execute_script("arguments[0].scrollIntoView();", resume_input)
#                 resume_input.send_keys(user_config["resume"])
#                 logging.info("Resume uploaded.")
#             except NoSuchElementException:
#                 logging.info("Resume upload field not found. Skipping.")

#             self.random_sleep()

#             text_areas = driver.find_elements(
#                 By.CSS_SELECTOR, locators.get("textareas", "textarea")
#             )
#             for text_area in text_areas:
#                 try:
#                     label = driver.find_element(
#                         By.CSS_SELECTOR, f"label[for='{text_area.get_attribute('id')}']"
#                     )
#                     question_text = label.text.strip()
#                     normalized_question = self.normalize_text(question_text)
#                     if normalized_question in qa_pairs:
#                         logging.info(f"Filling text area: {question_text}")
#                         text_area.send_keys(qa_pairs[normalized_question])
#                     else:
#                         logging.info(f"No answer found for question: {question_text}")
#                 except NoSuchElementException:
#                     continue

#             input_fields = driver.find_elements(
#                 By.CSS_SELECTOR, locators.get("input_fields", "")
#             )
#             for field in input_fields:
#                 try:
#                     aria_label = field.get_attribute("aria-label")
#                     if not aria_label:
#                         continue
#                     normalized_question = self.normalize_text(aria_label)
#                     if normalized_question in qa_pairs:
#                         logging.info(f"Filling input field: {aria_label}")
#                         field.clear()
#                         field.send_keys(qa_pairs[normalized_question])
#                     else:
#                         logging.info(f"No answer found for input field: {aria_label}")
#                 except Exception as e:
#                     logging.error(f"Error filling input field: {e}")

#             submit_button_selectors = locators.get("submit_buttons", [])
#             wait_time = 0
#             while True:
#                 try:
#                     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#                     time.sleep(2)
#                     submit_button_clicked = False
#                     for selector in submit_button_selectors:
#                         try:
#                             submit_button = driver.find_element(By.CSS_SELECTOR, selector)
#                             driver.execute_script(
#                                 "arguments[0].scrollIntoView();", submit_button
#                             )
#                             WebDriverWait(driver, 10).until(
#                                 EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
#                             )
#                             submit_button.click()
#                             logging.info(f"'Submit' button clicked using selector: {selector}")
#                             submit_button_clicked = True
#                             break
#                         except (
#                             NoSuchElementException,
#                             ElementNotInteractableException,
#                             StaleElementReferenceException,
#                         ):
#                             continue
#                     if not submit_button_clicked:
#                         logging.info("No 'Submit' button found.")
#                     time.sleep(8)
#                     error_elements = driver.find_elements(
#                         By.CSS_SELECTOR, locators.get("error_messages", "")
#                     )
#                     if not error_elements:
#                         logging.info("All required fields filled. Proceeding with submission.")
#                         break
#                     if wait_time == 0:
#                         logging.info(
#                             "Some required fields are missing! Please fill them manually."
#                         )
#                     self.random_sleep(15, 30)
#                     wait_time += 20
#                     if wait_time >= 60:
#                         logging.info(f"Waiting... {wait_time} seconds elapsed.")
#                 except Exception as e:
#                     logging.error(f"Error checking required fields: {e}")

#             try:
#                 WebDriverWait(driver, 10).until(EC.url_changes(driver.current_url))
#                 logging.info("Application submitted successfully.")
#                 self.log_result_to_csv(results_filename, url, "Success")
#             except TimeoutException:
#                 try:
#                     confirmation_xpath = locators.get("confirmation_xpath", "")
#                     confirmation_message = driver.find_element(By.XPATH, confirmation_xpath)
#                     if confirmation_message:
#                         logging.info("Application submitted (confirmation message found).")
#                         self.log_result_to_csv(results_filename, url, "Success")
#                 except NoSuchElementException:
#                     logging.error("Submission failed.")
#                     self.log_result_to_csv(results_filename, url, "Failed")

#         except Exception as e:
#             logging.error(f"Error while submitting: {e}")
#             self.log_result_to_csv(results_filename, url, "Failed")

#     def run(self):
#         users = self.list_users()
#         user_mapping = {str(i + 1): user for i, user in enumerate(users)}
#         print("Available users:", ", ".join([f"{num}-{user}" for num, user in user_mapping.items()]))

#         selected_number = input("Select a user by number: ").strip()
#         if selected_number not in user_mapping:
#             logging.error(f"Error: User number '{selected_number}' not found.")
#             return

#         selected_user = user_mapping[selected_number]
#         user_config = self.load_user_credentials(selected_user)
#         if not user_config:
#             return

#         resume_path = self.load_user_resume(selected_user)
#         if not resume_path:
#             return
#         user_config["resume"] = resume_path

#         logs_directory = "logs"
#         os.makedirs(logs_directory, exist_ok=True)
#         today_date = datetime.datetime.now().strftime("%Y-%m-%d")
#         results_filename = os.path.join(
#             logs_directory, f"grenhouse_application_{selected_user}_{today_date}.csv"
#         )
#         self.initialize_csv(results_filename)

#         job_urls = self.load_job_urls()
#         qa_pairs = self.load_qa_pairs()
#         locators = self.load_locators()
#         logging.info(f"Found {len(job_urls)} job(s) to apply for.")

#         for index, job_url in enumerate(job_urls, start=1):
#             logging.info(f"Applying for job {index}/{len(job_urls)}: {job_url}")
#             driver = setup_driver()
#             try:
#                 self.apply_greenhouse(driver, job_url, qa_pairs, locators, user_config)
#             except Exception as e:
#                 logging.error(f"Error applying to {job_url}: {e}")
#                 self.log_result_to_csv(results_filename, job_url, "Failed")
#             driver.quit()
#             self.random_sleep()

#         logging.info("All applications completed!")

class GreenhouseAutomation:
    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logging.basicConfig(
            filename="logs/greenhouse_terminal.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    def list_users(self, credentials_dir="credentials"):
        yaml_files = glob.glob(os.path.join(credentials_dir, "*.yaml"))
        users = [os.path.splitext(os.path.basename(file))[0] for file in yaml_files]
        return users

    def load_user_credentials(self, username, credentials_dir="credentials"):
        credentials_file = os.path.join(credentials_dir, f"{username}.yaml")
        return self.load_credentials(credentials_file)

    def load_user_resume(self, username, resume_dir="resume"):
        resume_file = os.path.join(resume_dir, f"{username}.pdf")
        if not os.path.exists(resume_file):
            logging.error(f"Error: Resume file '{resume_file}' not found for user '{username}'.")
            return None
        return os.path.abspath(resume_file)

    def load_credentials(self, filename):
        if not os.path.exists(filename):
            logging.error(f"Error: credentials file '{filename}' not found!")
            return None
        with open(filename, "r", encoding="utf-8") as file:
            credentials = yaml.safe_load(file)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            credentials["resume"] = os.path.abspath(os.path.join(base_dir, credentials["resume"]))
            return credentials

    def load_job_urls(self, filename="jobs/linkedin_jobs.csv"):
        job_urls = []
        if not os.path.exists(filename):
            logging.error(f"Error: The file '{filename}' was not found.")
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
                    logging.warning(f"Skipping job with missing data: {row}")
        return job_urls

    def normalize_text(self, text):
        return text.strip().lower().replace("*", "").replace(".", "").replace(" ", "")

    def load_qa_pairs(self, filename="config/greenhouse_answers.csv"):
        qa_pairs = {}
        if not os.path.exists(filename):
            logging.error(f"Error: The file '{filename}' was not found.")
            return qa_pairs
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    question = row[0].strip()
                    answer = row[1].strip()
                    qa_pairs[self.normalize_text(question)] = answer
        return qa_pairs

    def load_locators(self, filename="locators/greenhouse_locators.json"):
        if not os.path.exists(filename):
            logging.error(f"Error: Locators file '{filename}' not found!")
            return {}
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)

    def random_sleep(self, min_time=2, max_time=8):
        sleep_time = random.uniform(min_time, max_time)
        logging.info(f"Sleeping for {round(sleep_time, 2)} seconds.")
        time.sleep(sleep_time)

    def log_result_to_csv(self, filename, url, status):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([url, status, timestamp])

    def initialize_csv(self, filename):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["URL", "Status", "Timestamp"])

    def apply_greenhouse(self, driver, url, qa_pairs, locators, user_config, results_filename):
        logging.info(f"Applying to: {url}")
        driver.get(url)
        self.random_sleep()

        try:
            apply_button_selectors = locators.get("apply_buttons", [])
            apply_button_clicked = False
            for selector in apply_button_selectors:
                try:
                    apply_button = driver.find_element(By.XPATH, selector)
                    driver.execute_script("arguments[0].scrollIntoView();", apply_button)
                    apply_button.click()
                    logging.info(f"'Apply' button clicked using selector: {selector}")
                    apply_button_clicked = True
                    break
                except (NoSuchElementException, ElementNotInteractableException):
                    continue
            if not apply_button_clicked:
                logging.info("No 'Apply' button found. Proceeding with form filling.")
            self.random_sleep()

            fields = locators.get("fields", {})
            for key, field_id in fields.items():
                try:
                    field = driver.find_element(By.ID, field_id)
                    field.clear()
                    field.send_keys(user_config[key])
                    logging.info(f"{key} filled.")
                except NoSuchElementException:
                    logging.info(f"{key} field not found. It might be optional.")

            self.random_sleep()

            try:
                location_input = driver.find_element(
                    By.ID, locators.get("location_input", "")
                )
                location_input.clear()
                location_input.send_keys(user_config["location"])
                time.sleep(2)
                location_input.send_keys(Keys.ARROW_DOWN)
                location_input.send_keys(Keys.RETURN)
                logging.info(f"Location set to {user_config['location']} (dropdown selected)")
            except NoSuchElementException:
                logging.info("Location input field not found. Skipping.")

            self.random_sleep()

            try:
                resume_input = driver.find_element(
                    By.CSS_SELECTOR, locators.get("resume_input", "")
                )
                driver.execute_script("arguments[0].scrollIntoView();", resume_input)
                resume_input.send_keys(user_config["resume"])
                logging.info("Resume uploaded.")
            except NoSuchElementException:
                logging.info("Resume upload field not found. Skipping.")

            self.random_sleep()

            text_areas = driver.find_elements(
                By.CSS_SELECTOR, locators.get("textareas", "textarea")
            )
            for text_area in text_areas:
                try:
                    label = driver.find_element(
                        By.CSS_SELECTOR, f"label[for='{text_area.get_attribute('id')}']"
                    )
                    question_text = label.text.strip()
                    normalized_question = self.normalize_text(question_text)
                    if normalized_question in qa_pairs:
                        logging.info(f"Filling text area: {question_text}")
                        text_area.send_keys(qa_pairs[normalized_question])
                    else:
                        logging.info(f"No answer found for question: {question_text}")
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
                    normalized_question = self.normalize_text(aria_label)
                    if normalized_question in qa_pairs:
                        logging.info(f"Filling input field: {aria_label}")
                        field.clear()
                        field.send_keys(qa_pairs[normalized_question])
                    else:
                        logging.info(f"No answer found for input field: {aria_label}")
                except Exception as e:
                    logging.error(f"Error filling input field: {e}")

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
                            logging.info(f"'Submit' button clicked using selector: {selector}")
                            submit_button_clicked = True
                            break
                        except (
                            NoSuchElementException,
                            ElementNotInteractableException,
                            StaleElementReferenceException,
                        ):
                            continue
                    if not submit_button_clicked:
                        logging.info("No 'Submit' button found.")
                    time.sleep(8)
                    error_elements = driver.find_elements(
                        By.CSS_SELECTOR, locators.get("error_messages", "")
                    )
                    if not error_elements:
                        logging.info("All required fields filled. Proceeding with submission.")
                        break
                    if wait_time == 0:
                        logging.info(
                            "Some required fields are missing! Please fill them manually."
                        )
                    self.random_sleep(15, 30)
                    wait_time += 20
                    if wait_time >= 60:
                        logging.info(f"Waiting... {wait_time} seconds elapsed.")
                except Exception as e:
                    logging.error(f"Error checking required fields: {e}")

            try:
                WebDriverWait(driver, 10).until(EC.url_changes(driver.current_url))
                logging.info("Application submitted successfully.")
                self.log_result_to_csv(results_filename, url, "Success")
            except TimeoutException:
                try:
                    confirmation_xpath = locators.get("confirmation_xpath", "")
                    confirmation_message = driver.find_element(By.XPATH, confirmation_xpath)
                    if confirmation_message:
                        logging.info("Application submitted (confirmation message found).")
                        self.log_result_to_csv(results_filename, url, "Success")
                except NoSuchElementException:
                    logging.error("Submission failed.")
                    self.log_result_to_csv(results_filename, url, "Failed")

        except Exception as e:
            logging.error(f"Error while submitting: {e}")
            self.log_result_to_csv(results_filename, url, "Failed")

    def run(self):
        users = self.list_users()
        user_mapping = {str(i + 1): user for i, user in enumerate(users)}
        print("Available users:", ", ".join([f"{num}-{user}" for num, user in user_mapping.items()]))

        selected_number = input("Select a user by number: ").strip()
        if selected_number not in user_mapping:
            logging.error(f"Error: User number '{selected_number}' not found.")
            return

        selected_user = user_mapping[selected_number]
        user_config = self.load_user_credentials(selected_user)
        if not user_config:
            return

        resume_path = self.load_user_resume(selected_user)
        if not resume_path:
            return
        user_config["resume"] = resume_path

        logs_directory = "logs"
        os.makedirs(logs_directory, exist_ok=True)
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        results_filename = os.path.join(
            logs_directory, f"grenhouse_application_{selected_user}_{today_date}.csv"
        )
        self.initialize_csv(results_filename)

        job_urls = self.load_job_urls()
        qa_pairs = self.load_qa_pairs()
        locators = self.load_locators()
        logging.info(f"Found {len(job_urls)} job(s) to apply for.")

        for index, job_url in enumerate(job_urls, start=1):
            logging.info(f"Applying for job {index}/{len(job_urls)}: {job_url}")
            driver = setup_driver()
            try:
                self.apply_greenhouse(driver, job_url, qa_pairs, locators, user_config, results_filename)
            except Exception as e:
                logging.error(f"Error applying to {job_url}: {e}")
                self.log_result_to_csv(results_filename, job_url, "Failed")
            driver.quit()
            self.random_sleep()

        logging.info("All applications completed!")



class JobviteAutomation:
    def __init__(self):
        self.setup_logging()
        self.interacted_elements = set()

    def setup_logging(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logging.basicConfig(
            filename="logs/jobvite_terminal.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    def get_logger(self):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        date_str = datetime.datetime.now().strftime("%d-%m-%Y")
        log_filename = f"jobvite_{date_str}.log"
        log_file_path = os.path.join(log_dir, log_filename)
        logger = logging.getLogger("JobStatusLogger")

        if not logger.handlers:
            logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def logger_log_job_status(self, job_link, status, candidate_name):
        logger = self.get_logger()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}], {candidate_name}, {status}, {job_link}"
        logger.info(log_entry)

    def load_applied_jobs(self):
        if os.path.exists("logs/jobvite_applied_jobs.yaml"):
            with open("logs/jobvite_applied_jobs.yaml", "r") as file:
                return yaml.safe_load(file) or {}
        return {}

    def save_applied_jobs(self, data):
        with open("logs/jobvite_applied_jobs.yaml", "w") as file:
            yaml.dump(data, file)

    def log_job_status(self, job_link, status, candidate_name):
        jobs_data = self.load_applied_jobs()
        jobs_data[job_link] = status
        self.save_applied_jobs(jobs_data)
        self.logger_log_job_status(job_link, status, candidate_name)

    def generate_job_links(self, csv_filename):
        job_links = []

        try:
            with open(csv_filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    company = row.get("company", "").strip()
                    job_id = row.get("job_id", "").strip()
                    fallback_url = row.get("platform_link", "").strip()
                    platform = row.get("platform", "").strip().lower()

                    final_url = None

                    if platform == "jobvite":
                        if company and job_id:
                            final_url = f"https://jobs.jobvite.com/{company}/job/{job_id}"
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

    def read_csv(self, file_path):
        qa_dict = {}
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                question = row["question"].strip()
                answer = row["answer"].strip()
                qa_dict[question] = answer
        return qa_dict

    def fill_form(self, driver, qa_data, filled_fields, filled_locators):
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

                radio_buttons = label_element.find_elements(By.XPATH, "following::input[@type='radio']")
                if radio_buttons:
                    for rb in radio_buttons:
                        if rb.get_attribute("value").strip().lower() == answer.strip().lower():
                            driver.execute_script("arguments[0].click();", rb)
                            completed_questions.add(question)
                            filled_fields.add(question)
                            break
                    continue

                input_element = None
                try:
                    input_element = label_element.find_element(By.XPATH, "following::*[self::input or self::textarea or self::select][1]")
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
                logging.warning(f"Skipping question '{question}' - Element not found or error: {e}")

        if len(completed_questions) == len(qa_data):
            logging.info("All questions have been filled. Stopping execution.")

        filled_locators.update(filled_fields)

    def interact_with_element(self, driver, css_selector, element_type, value=None, filled_locators=None):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            if element in self.interacted_elements or (filled_locators and css_selector in filled_locators):
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

            self.interacted_elements.add(element)
            if filled_locators is not None:
                filled_locators.add(css_selector)
            return True

        except Exception as e:
            logging.error(f"Error interacting with element ({css_selector}): {e}")
            return False

    def execute_automation(self, driver, locators, filled_locators):
        for key, locator in locators.items():
            self.interact_with_element(driver, locator["selector"], locator["type"], locator.get("value", ""), filled_locators)

    def wait_until_all_required_filled(self, driver):
        while True:
            required_fields = driver.find_elements(By.CSS_SELECTOR, "input[required], select[required], textarea[required]")
            unfilled_fields = [field for field in required_fields if not field.get_attribute("value")]

            if not unfilled_fields:
                logging.info("All required fields are filled. Proceeding...")
                return

            for field in unfilled_fields:
                logging.info(f"Waiting for required field: {field.get_attribute('label') or field.get_attribute('id') or 'Unknown Field'}")

            time.sleep(5)

    def handle_uninteracted_required_elements(self, driver, config, filled_locators):
        all_form_elements = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
        for element in all_form_elements:
            if element not in self.interacted_elements:
                try:
                    is_required = element.get_attribute("required") is not None
                    if is_required and not element.get_attribute("value"):
                        element.clear()
                        element.send_keys(config.get(element.get_attribute("name"), ""))
                        self.interacted_elements.add(element)
                        if filled_locators is not None:
                            filled_locators.add(element.get_attribute("name"))
                except Exception as e:
                    logging.error(f"Error processing required element: {e}")

    def upload_resume(self, driver, resume_path):
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

    def apply_to_job(self, driver, wait, job_id, job_link, resume_path, locators, config, candidate_name):
        logging.info(f"Opening job link: {job_link}")
        driver.get(job_link)

        filled_locators = set()

        try:
            apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Apply') or contains(@class, 'apply-button')]")))
            apply_button.click()
            logging.info("Clicked Apply button.")
            time.sleep(5)

            filled_fields = set()

            elements = driver.find_elements(By.XPATH, '//*[@required="required"]')

            for element in elements:
                element_id = element.get_attribute("id")
                element_value = element.get_attribute("value") or element.get_attribute("name")
                autocomplete_attr = element.get_attribute("autocomplete")

                logging.info(f"ID: {element_id}, Value: {element_value}, Autocomplete: {autocomplete_attr}")

                label = None
                for i in range(1, 6):
                    label_xpath = f'./ancestor::*[{i}]/label'
                    label_element = element.find_elements(By.XPATH, label_xpath)
                    if label_element:
                        label = label_element[0].text
                        break

                label_text = label if label else "No label found"

                logging.info(f"ID: {element_id}, Value: {element_value}, Nearest Label: {label_text}")

            select_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Select')]")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_button)
            time.sleep(1)

            try:
                select_button.click()
                logging.info("Clicked Select button for resume upload.")
            except Exception as e:
                logging.warning(f"Click intercepted. Trying JavaScript click instead. Error: {e}")
                driver.execute_script("arguments[0].click();", select_button)

            time.sleep(2)

            self.upload_resume(driver, resume_path)

            self.execute_automation(driver, locators, filled_locators)
            self.handle_uninteracted_required_elements(driver, config, filled_locators)
            qa_data = self.read_csv("config/jobvite_answers.csv")
            self.fill_form(driver, qa_data, filled_fields, filled_locators)
            self.wait_until_all_required_filled(driver)

            next_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, "button.jv-button.jv-button-primary.jv-button-large"
            )))
            next_button.click()
            logging.info("Clicked Next button.")
            time.sleep(5)

            # self.execute_automation(driver, locators, filled_locators)
            self.handle_uninteracted_required_elements(driver, config, filled_locators)
            qa_data = self.read_csv("config/jobvite_answers.csv")
            self.fill_form(driver, qa_data, filled_fields, filled_locators)
            self.wait_until_all_required_filled(driver)

            try:
                next_button = wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button.jv-button.jv-button-primary.jv-button-large"
                )))
                next_button.click()
                logging.info("Clicked the Next button proceeding to the next page.")
                time.sleep(5)
                logging.info("Clicked the Next button proceeding to the next page.")

                # self.execute_automation(driver, locators, filled_locators)
                self.handle_uninteracted_required_elements(driver, config, filled_locators)
                qa_data = self.read_csv("config/jobvite_answers.csv")
                self.fill_form(driver, qa_data, filled_fields, filled_locators)
                self.wait_until_all_required_filled(driver)

            except:
                send_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jv-button-primary') and contains(., 'Send Application')]")))
                driver.execute_script("arguments[0].click();", send_button)
                logging.info("No Next button found, clicked Send Application.")

            send_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jv-button-primary') and contains(., 'Send Application')]")))
            driver.execute_script("arguments[0].click();", send_button)
            logging.info("Clicked 'Send Application' button.")

            try:
                confirmation_message = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "h2.jv-page-message-header"
                )))
                logging.info("Application submitted successfully!")
                self.log_job_status(job_link, "Successfully Applied", candidate_name)

            except TimeoutException:
                try:
                    already_applied_message = wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, "p.jv-page-error-header"
                    )))
                    logging.info("You have already submitted the application.")
                    self.log_job_status(job_link, "Already Submitted", candidate_name)

                except TimeoutException:
                    logging.error("Unable to submit the application and no confirmation message found.")
                    self.log_job_status(job_link, "Submission Failed", candidate_name)

        except TimeoutException:
            logging.error(f"Timeout: Could not find elements for job {job_link}")
            self.log_job_status(job_link, "Failed", candidate_name)
        except NoSuchElementException as e:
            logging.error(f"Error applying for job: {e}")
            self.log_job_status(job_link, "Failed", candidate_name)

    def list_user_configs(self):
        config_dir = "credentials"
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.yaml')]
        if not config_files:
            logging.error("No user configuration files found.")
            exit(1)

        print("Available user configurations:")
        for idx, config_file in enumerate(config_files, start=1):
            print(f"{idx}. {config_file}")

        return config_files

    def select_user_config(self, config_files):
        try:
            choice = int(input("Select a user configuration by number: "))
            if 1 <= choice <= len(config_files):
                return config_files[choice - 1]
            else:
                logging.error("Invalid selection.")
                exit(1)
        except ValueError:
            logging.error("Invalid input. Please enter a number.")
            exit(1)

    def run(self):
        config_files = self.list_user_configs()
        selected_config = self.select_user_config(config_files)
        config_path = os.path.join("credentials", selected_config)

        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        candidate_name = config.get("first_name", "Unknown Candidate")
        logging.info(f"Candidate Name: {candidate_name}")

        resume_filename = config.get("resume_file", selected_config.replace('.yaml', '.txt'))
        resume_path = os.path.join("resume", resume_filename)

        if not os.path.isfile(resume_path):
            logging.error(f"Resume file not found at {resume_path}")
            exit(1)

        with open("locators/jobvite_locators.json", "r") as f:
            locators = json.load(f)

        for key in locators.keys():
            if key in config:
                locators[key]["value"] = config[key]

        for key, locator in locators.items():
            placeholder = f"{{{{ {key.replace('_', ' ')} }}}}"
            if locator.get("value") == placeholder:
                locator["value"] = config.get(key.replace("_", " "), "")

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = setup_driver()
        wait = WebDriverWait(driver, 20)

        applied_jobs = self.load_applied_jobs()
        job_links = self.generate_job_links("jobs/linkedin_jobs.csv")

        for job in job_links:
            job_id = job["job_id"]
            job_link = job["url"]

            if job_link in applied_jobs and applied_jobs[job_link] == "Successfully Applied":
                logging.info(f"Skipping already applied job: {job_id}")
                continue

            self.apply_to_job(driver, wait, job_id, job_link, resume_path, locators, config, candidate_name)

        driver.quit()

class LeverAutomation:
    def __init__(self):
        self.lever_base_url = "https://jobs.lever.co"
        self.profile_yaml = self.select_profile()
        self.candidate_name = os.path.splitext(self.profile_yaml)[0]
        self.load_locators()
        self.credentials = self.load_config(f"credentials/{self.profile_yaml}")
        self.answers = self.load_answers("config/lever_answers.csv")
        self.driver = setup_driver()

    def select_profile(self):
        config_dir = "credentials"
        yaml_files = [
            f for f in os.listdir(config_dir)
            if os.path.isfile(os.path.join(config_dir, f)) and f.lower().endswith(('.yaml', '.yml'))
        ]

        if not yaml_files:
            logging.error("No YAML files found in configuration directory.")
            raise FileNotFoundError("No YAML files found in configuration.")

        yaml_files.sort()
        print("Select a profile:")
        for idx, yaml_file in enumerate(yaml_files, 1):
            print(f"{idx} = {yaml_file}")

        while True:
            try:
                choice = input(f"Enter profile number (1-{len(yaml_files)}): ").strip()
                profile_num = int(choice)
                if 1 <= profile_num <= len(yaml_files):
                    selected_yaml = yaml_files[profile_num - 1]
                    logging.info(f"Selected profile: {selected_yaml}")
                    return selected_yaml
                else:
                    print(f"Please enter a number between 1 and {len(yaml_files)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

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

    def load_config(self, file_location):
        try:
            with open(file_location, 'r') as stream:
                data = yaml.safe_load(stream)
        except FileNotFoundError:
            logging.error(f"Config file '{file_location}' not found.")
            raise
        except yaml.YAMLError as exc:
            logging.error(f"Error parsing YAML file: {exc}")
            raise

        required_fields = ["full_name", "email", "phone", "linkedin", "resume_path", "current_company", "current_location"]
        credentials = {}

        for field in required_fields:
            if field not in data:
                logging.error(f"Required field '{field}' missing in YAML.")
                raise KeyError(f"Required field '{field}' missing in YAML.")
            credentials[field] = str(data[field])

        phone = credentials["phone"]
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        if not re.match(r"^\+?\d{8,15}$", cleaned_phone):
            logging.warning(f"Phone number format warning (continuing anyway): {phone}")

        credentials["github"] = str(data.get("github", ""))
        credentials["portfolio"] = str(data.get("portfolio", ""))
        credentials["work_status"] = str(data.get("work_status", ""))

        base_dir = os.path.dirname(os.path.abspath(__file__))
        resume_path = os.path.join(base_dir, credentials["resume_path"])
        if not os.path.isfile(resume_path):
            logging.error(f"Resume file not found at: {resume_path}")
            raise FileNotFoundError(f"Resume file not found at: {resume_path}")
        credentials["resume"] = resume_path

        return credentials

    def load_answers(self, file_path):
        answers = {}
        try:
            with open(file_path, mode="r", encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    question = row["Question"].strip().lower()
                    answers[question] = row["Answer"].strip()
            return answers
        except FileNotFoundError:
            logging.error(f"Answers file '{file_path}' not found.")
            raise

    def save_session_state(self, job_link):
        session_data = {
            "current_url": self.driver.current_url,
            "cookies": self.driver.get_cookies(),
            "timestamp": datetime.datetime.now().isoformat()
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

    def normalize_text(self, text):
        if not text:
            return ""
        return re.sub(r"[^a-zA-Z0-9\s]", "", text).strip().lower()

    def validate_required_fields(self):
        required_fields = ["full_name", "email", "phone", "resume"]
        missing_fields = []

        for field in required_fields:
            if not self.credentials.get(field):
                missing_fields.append(field)

        if missing_fields:
            logging.error(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        return True

    def check_required_fields_filled(self):
        try:
            required_fields = []

            for selector in (
                self.locators["FIELD_SELECTORS"].get("full_name", []) +
                self.locators["FIELD_SELECTORS"].get("email", []) +
                self.locators["FIELD_SELECTORS"].get("phone", []) +
                self.locators["FIELD_SELECTORS"].get("linkedin", []) +
                self.locators["QUESTION_FIELD_SELECTORS"].get("text_input", []) +
                self.locators["QUESTION_FIELD_SELECTORS"].get("textarea", [])
            ):
                selector_type = selector.get('type', 'css')
                selector_value = selector.get('value', '')
                try:
                    by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                    elements = self.driver.find_elements(by_type, selector_value)
                    for element in elements:
                        is_required = (
                            element.get_attribute("required") is not None or
                            any(
                                self.driver.find_elements(
                                    By.XPATH,
                                    f".//ancestor::*[contains(., '{indicator}')]"
                                )
                                for indicator in self.locators["QUESTION_FIELD_SELECTORS"]["required_indicator"]
                            )
                        )
                        if is_required:
                            required_fields.append({"element": element, "type": "text"})
                except Exception as e:
                    logging.warning(f"Error checking selector {selector_value}: {str(e)}")

            for selector in self.locators["QUESTION_FIELD_SELECTORS"].get("dropdown", []):
                selector_type = selector.get('type', 'css')
                selector_value = selector.get('value', '')
                try:
                    by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                    elements = self.driver.find_elements(by_type, selector_value)
                    for element in elements:
                        is_required = (
                            element.get_attribute("required") is not None or
                            any(
                                self.driver.find_elements(
                                    By.XPATH,
                                    f".//ancestor::*[contains(., '{indicator}')]"
                                )
                                for indicator in self.locators["QUESTION_FIELD_SELECTORS"]["required_indicator"]
                            )
                        )
                        if is_required:
                            required_fields.append({"element": element, "type": "dropdown"})
                except Exception as e:
                    logging.warning(f"Error checking dropdown selector {selector_value}: {str(e)}")

            checkbox_groups = {}
            for selector in self.locators["QUESTION_FIELD_SELECTORS"].get("checkbox", []):
                selector_type = selector.get('type', 'css')
                selector_value = selector.get('value', '')
                try:
                    by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                    checkboxes = self.driver.find_elements(by_type, selector_value)
                    for checkbox in checkboxes:
                        parent_question = checkbox.find_element(
                            By.XPATH, "./ancestor::li[contains(@class, 'application-question') or contains(@class, 'question')]"
                        )
                        question_text = parent_question.text.strip() or "Unknown question"
                        is_required = any(
                            indicator in question_text
                            for indicator in self.locators["QUESTION_FIELD_SELECTORS"]["required_indicator"]
                        )
                        if is_required:
                            if question_text not in checkbox_groups:
                                checkbox_groups[question_text] = []
                            checkbox_groups[question_text].append(checkbox)
                except Exception as e:
                    logging.warning(f"Error checking checkbox selector {selector_value}: {str(e)}")

            for field in required_fields:
                element = field["element"]
                field_type = field["type"]
                try:
                    if field_type in ["text", "textarea"]:
                        value = element.get_attribute("value")
                        if not value or value.strip() == "":
                            logging.warning(f"Required {field_type} field is empty: {element.get_attribute('name') or element.get_attribute('id')}")
                            return False
                    elif field_type == "dropdown":
                        select = Select(element)
                        if not select.first_selected_option or select.first_selected_option.text.strip() == "":
                            logging.warning(f"Required dropdown field is not selected: {element.get_attribute('name') or element.get_attribute('id')}")
                            return False
                except Exception as e:
                    logging.warning(f"Error checking {field_type} field: {str(e)}")
                    return False

            for question_text, checkboxes in checkbox_groups.items():
                if not any(cb.is_selected() for cb in checkboxes):
                    logging.warning(f"Required checkbox group '{question_text}' has no selections")
                    return False

            logging.info("All required fields are filled")
            return True

        except Exception as e:
            logging.error(f"Error checking required fields: {str(e)}")
            return False

    def find_element(self, locator_key, sub_key=None, multiple=False, timeout=10):
        if sub_key:
            selectors = self.locators.get(locator_key, {}).get(sub_key, [])
        else:
            selectors = self.locators.get(locator_key, [])
        if not isinstance(selectors, list):
            selectors = [selectors]
        logging.info(f"Trying selectors for {locator_key}{'.' + sub_key if sub_key else ''}: {[s['value'] for s in selectors]}")

        for selector in selectors:
            selector_type = selector.get('type', 'css')
            selector_value = selector.get('value', '')
            logging.info(f"Attempting {selector_type} selector: {selector_value}")

            try:
                by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                if multiple:
                    return WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_all_elements_located((by_type, selector_value)))
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by_type, selector_value)))
            except TimeoutException:
                logging.warning(f"Timeout {selector_type} selector {selector_value}")
                continue
            except NoSuchElementException:
                logging.warning(f"Element not found for {selector_type} selector {selector_value}")
                continue
            except ElementNotInteractableException:
                logging.warning(f"Element not interactable for {selector_type} selector {selector_value}")
                continue
            except Exception as e:
                logging.warning(f"Unexpected error for {selector_type} selector {selector_value}: {str(e)}")
                continue
        logging.error(f"No selectors worked for {locator_key}{'.' + sub_key if sub_key else ''}")
        return None

    def upload_resume(self):
        value = self.credentials["resume"]
        logging.info(f"Attempting to upload resume: {value}")

        resume_input = self.find_element("resume_path")
        if not resume_input:
            logging.warning("Resume file input not found, it may be optional")
            return False

        logging.info(f"Found resume input: {resume_input.get_attribute('outerHTML')}")

        try:
            upload_button = self.find_element("resume_upload_button")
            if upload_button:
                logging.info(f"Upload button found: {upload_button.get_attribute('outerHTML')}")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", upload_button)
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
                resume_input
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
            confirmation_selectors = [s['value'] for s in self.locators.get("resume_upload_confirmation", []) if s['type'] == 'css']
            if confirmation_selectors:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ", ".join(confirmation_selectors)))
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

    def open_job_and_click_apply(self, job_link):
        logging.info(f"Opening job: {job_link}")
        self.driver.get(job_link)
        time.sleep(2)

        if any(text in self.driver.page_source for text in ["404", "Not Found", "Page not found"]):
            logging.warning("Page not found (404)")
            return "404"

        if "already applied" in self.driver.page_source.lower():
            logging.info("Job already applied to")
            return "already applied"

        if "apply" in self.driver.current_url.lower():
            logging.info("Direct job application form detected")
            return True

        for selector in self.locators["APPLY_SELECTORS"]:
            selector_type = selector.get('type', 'css')
            selector_value = selector.get('value', '')
            logging.info(f"Attempting {selector_type} selector for apply button: {selector_value}")
            try:
                by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                apply_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by_type, selector_value)))
                self.driver.execute_script("arguments[0].scrollIntoView();", apply_button)
                self.driver.execute_script("arguments[0].click();", apply_button)
                logging.info(f"Clicked 'Apply' button using {selector_type} selector")
                time.sleep(3)
                return True
            except (TimeoutException, NoSuchElementException):
                logging.warning(f"Failed to click apply button with {selector_type} selector")
                continue

        logging.warning("No 'Apply' button found")
        return False

    def fill_basic_fields(self):
        self.upload_resume()

        filled_fields = set()

        for field_key, selectors in self.locators["FIELD_SELECTORS"].items():
            if field_key in ["resume", "resume_path", "resume_upload_button", "resume_upload_confirmation"]:
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
                selector_type = selector.get('type', 'css')
                selector_value = selector.get('value', '')
                try:
                    by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                    input_field = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((by_type, selector_value))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                    input_field.clear()
                    input_field.send_keys(value)
                    logging.info(f"Filled {field_key}: {value}")
                    filled_fields.add(field_key)
                    break
                except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                    logging.warning(f"Failed to fill {field_key} with {selector_type} selector {selector_value}: {str(e)}")
                    continue

    def handle_location_dropdown(self):
        try:
            location_input = self.find_element("LOCATION_SELECTORS", "input")
            if location_input:
                is_required = False
                parent_elements = self.driver.find_elements(By.XPATH, ".//ancestor::*[contains(., '*')]")
                for parent in parent_elements:
                    if any(indicator in parent.text for indicator in self.locators["QUESTION_FIELD_SELECTORS"]["required_indicator"]):
                        is_required = True
                        break

                location_value = str(self.credentials["current_location"])
                logging.info(f"Attempting to fill location with: {location_value}")
                location_input.click()
                location_input.clear()
                location_input.send_keys(location_value)
                logging.info(f"Filled location with: {location_value}")
                time.sleep(1)

                try:
                    options = self.find_element("LOCATION_SELECTORS", "options", multiple=True)
                    if options:
                        for option in options:
                            if location_value.lower() in option.text.lower():
                                option.click()
                                logging.info(f"Selected location option: {option.text}")
                                break
                        else:
                            logging.info("No matching location option found")
                    elif is_required:
                        logging.warning("Location is required but no dropdown options found")
                except Exception as e:
                    logging.info(f"No location dropdown options available: {str(e)}")
            else:
                logging.info("No location input found")
        except Exception as e:
            logging.warning(f"Location dropdown handling failed: {str(e)}")

    def handle_radio_buttons(self, question_element, answer, question_text):
        radio_buttons = []
        for selector in self.locators["QUESTION_FIELD_SELECTORS"]["radio_button"]:
            try:
                radio_buttons.extend(
                    question_element.find_elements(
                        By.CSS_SELECTOR if selector["type"] == "css" else By.XPATH,
                        selector["value"]
                    )
                )
            except NoSuchElementException:
                continue

        if not radio_buttons:
            logging.warning(f"No radio buttons found for question: {question_text}")
            return False

        normalized_answer = self.normalize_text(answer)
        logging.info(f"Radio button options for '{question_text}': {[rb.get_attribute('value') or rb.text for rb in radio_buttons]}")

        for radio in radio_buttons:
            try:
                value = self.normalize_text(radio.get_attribute("value") or radio.text)
                if value == normalized_answer:
                    if not radio.is_selected():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", radio)
                        self.driver.execute_script("arguments[0].click();", radio)
                        logging.info(f"Selected radio button: '{value}' for '{question_text}'")
                    return True
            except (StaleElementReferenceException, ElementNotInteractableException) as e:
                logging.warning(f"Error interacting with radio button: {str(e)}")
                continue

        best_match = None
        best_score = 0
        for radio in radio_buttons:
            try:
                value = self.normalize_text(radio.get_attribute("value") or radio.text)
                score = fuzz.ratio(value, normalized_answer)
                if score > 80 and score > best_score:
                    best_match = radio
                    best_score = score
            except StaleElementReferenceException:
                continue

        if best_match:
            try:
                if not best_match.is_selected():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", best_match)
                    self.driver.execute_script("arguments[0].click();", best_match)
                logging.info(f"Selected radio button (fuzzy): '{best_match.get_attribute('value') or best_match.text}' (Score: {best_score}) for '{question_text}'")
                return True
            except (ElementNotInteractableException, StaleElementReferenceException) as e:
                logging.warning(f"Failed to select fuzzy-matched radio button: {str(e)}")

        logging.warning(f"No matching radio button found for answer '{answer}' in question '{question_text}'")
        return False

    def handle_checkboxes(self, question_element, question_text):
        checkboxes = []
        for selector in self.locators["QUESTION_FIELD_SELECTORS"]["checkbox"]:
            try:
                checkboxes.extend(
                    question_element.find_elements(
                        By.CSS_SELECTOR if selector["type"] == "css" else By.XPATH,
                        selector["value"]
                    )
                )
            except NoSuchElementException:
                continue

        if not checkboxes:
            logging.info(f"No checkboxes found for question: {question_text}")
            return False

        normalized_question = self.normalize_text(question_text)
        logging.info(f"Checkboxes found for '{question_text}': {[cb.get_attribute('name') or cb.text for cb in checkboxes]}")

        is_required = any(indicator in question_text for indicator in self.locators["QUESTION_FIELD_SELECTORS"]["required_indicator"])

        for checkbox in checkboxes:
            try:
                label = None
                try:
                    label_element = checkbox.find_element(
                        By.XPATH, "./following-sibling::label | ./preceding-sibling::label | ./parent::label"
                    )
                    label = label_element.text.strip()
                except NoSuchElementException:
                    label = checkbox.get_attribute("name") or checkbox.get_attribute("value") or ""

                if not label:
                    logging.info(f"Skipping checkbox with no label for question: {question_text}")
                    continue

                normalized_label = self.normalize_text(label)
                logging.info(f"Evaluating checkbox with label: '{label}' (required: {is_required})")

                if "linkedin" in normalized_question or "linkedin" in normalized_label:
                    if self.credentials["linkedin"]:
                        if not checkbox.is_selected():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                            self.driver.execute_script("arguments[0].click();", checkbox)
                            logging.info(f"Checked LinkedIn checkbox for '{question_text}' with label '{label}'")
                        return True
                    else:
                        logging.info(f"Skipping LinkedIn checkbox for '{question_text}' (no LinkedIn URL provided)")
                        continue

                best_match = None
                best_score = 0
                for answer_key, answer_value in self.answers.items():
                    score = fuzz.ratio(self.normalize_text(answer_key), normalized_label)
                    if score > best_score:
                        best_match = answer_key
                        best_score = score

                if best_match and best_score > 90:
                    normalized_answer = self.normalize_text(self.answers[best_match])
                    if normalized_answer in ["yes", "true", "agree", "accept", "confirm"]:
                        if not checkbox.is_selected():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                            self.driver.execute_script("arguments[0].click();", checkbox)
                            logging.info(f"Checked checkbox for '{question_text}' with label '{label}' (fuzzy match, score: {best_score})")
                        return True
                    else:
                        logging.info(f"Skipping checkbox for '{question_text}' with label '{label}' (answer: {self.answers[best_match]})")
                else:
                    if is_required:
                        logging.warning(f"Required checkbox for '{question_text}' with label '{label}' not matched (best score: {best_score})")
                    else:
                        logging.info(f"No matching answer for checkbox with label '{label}' (best score: {best_score})")

            except (ElementNotInteractableException, StaleElementReferenceException) as e:
                logging.warning(f"Failed to interact with checkbox for '{question_text}': {str(e)}")
                continue

        logging.info(f"No relevant checkboxes checked for '{question_text}'")
        return False

    def handle_custom_questions(self):
        question_elements = self.find_element("QUESTION_SELECTORS", multiple=True) or []
        logging.info(f"Found {len(question_elements)} question elements")

        for question_element in question_elements:
            try:
                label = None
                for selector in self.locators["QUESTION_FIELD_SELECTORS"]["label"]:
                    try:
                        label = question_element.find_element(
                            By.CSS_SELECTOR if selector["type"] == "css" else By.XPATH,
                            selector["value"]
                        )
                        break
                    except NoSuchElementException:
                        continue
                question_text = label.text.strip() if label else question_element.text.strip() or "Unknown question"
                logging.info(f"Processing question: {question_text}")

                normalized_question = self.normalize_text(question_text)

                if any(keyword in normalized_question for keyword in ["resume", "cv", "upload file"]):
                    logging.info(f"Skipping resume question: {question_text}")
                    continue

                best_match = None
                best_score = 0
                for q in self.answers:
                    score = fuzz.ratio(self.normalize_text(q), normalized_question)
                    if score > best_score:
                        best_match = q
                        best_score = score

                if best_match and best_score > 70:
                    answer = self.answers[best_match]
                    logging.info(f"Matched '{question_text}' to '{best_match}' (Score: {best_score})")

                    for selector in self.locators["QUESTION_FIELD_SELECTORS"]["textarea"]:
                        try:
                            textarea = question_element.find_element(
                                By.CSS_SELECTOR if selector["type"] == "css" else By.XPATH,
                                selector["value"]
                            )
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", textarea)
                            textarea.clear()
                            textarea.send_keys(answer)
                            logging.info(f"Filled textarea with: {answer} for '{question_text}'")
                            break
                        except (NoSuchElementException, ElementNotInteractableException):
                            continue

                    for selector in self.locators["QUESTION_FIELD_SELECTORS"]["text_input"]:
                        try:
                            text_input = question_element.find_element(
                                By.CSS_SELECTOR if selector["type"] == "css" else By.XPATH,
                                selector["value"]
                            )
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", text_input)
                            text_input.clear()
                            text_input.send_keys(answer)
                            logging.info(f"Filled text input with: {answer} for '{question_text}'")
                            break
                        except (NoSuchElementException, ElementNotInteractableException):
                            continue

                    for selector in self.locators["QUESTION_FIELD_SELECTORS"]["dropdown"]:
                        try:
                            select_element = question_element.find_element(
                                By.CSS_SELECTOR if selector["type"] == "css" else By.XPATH,
                                selector["value"]
                            )
                            select = Select(select_element)
                            select.select_by_visible_text(answer)
                            logging.info(f"Selected dropdown option: {answer} for '{question_text}'")
                            break
                        except (NoSuchElementException, ElementNotInteractableException):
                            continue

                    if self.handle_radio_buttons(question_element, answer, question_text):
                        continue

                    if self.handle_checkboxes(question_element, question_text):
                        continue

                    logging.warning(f"Could not answer question: {question_text}")
                else:
                    if self.handle_checkboxes(question_element, question_text):
                        continue
                    logging.warning(f"No match found for question: {question_text}")
            except Exception as e:
                logging.warning(f"Error processing question '{question_text}': {str(e)}")

    def handle_acknowledgements(self):
        for selector in self.locators["ACKNOWLEDGEMENT_SELECTORS"]:
            selector_type = selector.get('type', 'css')
            selector_value = selector.get('value', '')
            if "required" in selector_value:
                logging.info(f"Skipping required acknowledgement checkbox to avoid overlap: {selector_value}")
                continue
            try:
                by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                checkbox = self.driver.find_element(by_type, selector_value)
                label = None
                try:
                    label_element = checkbox.find_element(
                        By.XPATH, "./following-sibling::label | ./preceding-sibling::label | ./parent::label"
                    )
                    label = label_element.text.strip()
                except NoSuchElementException:
                    label = checkbox.get_attribute("name") or checkbox.get_attribute("value") or "No label"

                if not checkbox.is_selected():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    logging.info(f"Checked acknowledgement checkbox with label '{label}' using {selector_type} selector {selector_value}")
            except NoSuchElementException:
                logging.info(f"No acknowledgement checkbox found with {selector_type} selector {selector_value}")
                continue
            except Exception as e:
                logging.warning(f"Error handling acknowledgement checkbox with {selector_type} selector {selector_value}: {str(e)}")

    def verify_submission(self, timeout=10):
        try:
            success_selectors = [
                "div.post-apply-message",
                "div.success-message",
                "div.application-submitted"
            ]
            for selector in success_selectors:
                try:
                    if WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    ):
                        return True
                except TimeoutException:
                    continue

            success_url_patterns = [
                "thanks",
                "success",
                "submitted"
            ]
            current_url = self.driver.current_url.lower()
            if any(pattern in current_url for pattern in success_url_patterns):
                return True

            return False
        except Exception as e:
            logging.error(f"Submission verification failed: {str(e)}")
            return False

    def submit_application(self):
        for selector in self.locators["SUBMIT_SELECTORS"]:
            selector_type = selector.get('type', 'css')
            selector_value = selector.get('value', '')
            try:
                by_type = By.CSS_SELECTOR if selector_type == 'css' else By.XPATH
                submit_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by_type, selector_value)))
                self.driver.execute_script("arguments[0].scrollIntoView();", submit_button)
                self.driver.execute_script("arguments[0].click();", submit_button)
                logging.info(f"Form submitted successfully with {selector_type} selector {selector_value}")
                return True
            except (TimeoutException, NoSuchElementException):
                logging.warning(f"Failed to submit with {selector_type} selector {selector_value}")
                continue
        logging.warning("No submit button found")
        return False

    def process_job_application(self, job_link, max_retries=2):
        job_id = job_link.split('/')[-1]
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
                    return "failed - missing required fields in credentials"

                self.fill_basic_fields()
                self.handle_location_dropdown()
                self.handle_custom_questions()
                self.handle_acknowledgements()

                logging.info("Pausing for 1.5 minutes for manual review...")
                time.sleep(90)

                max_wait_time = 600
                wait_interval = 30
                elapsed_time = 0
                while elapsed_time < max_wait_time:
                    if self.check_required_fields_filled():
                        logging.info("All required fields filled, proceeding to submit")
                        break
                    logging.info("Some required fields not filled. Waiting 30 seconds for user input...")
                    time.sleep(wait_interval)
                    elapsed_time += wait_interval

                if elapsed_time >= max_wait_time and not self.check_required_fields_filled():
                    logging.error("Timeout: Not all required fields filled within maximum wait time")
                    return "failed - required fields not filled"

                if self.submit_application():
                    if self.verify_submission():
                        return "success"
                    return "failed - submission verification failed"
                return "failed - submission failed"

            except WebDriverException as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    time.sleep(5)
                    self.driver.quit()
                    self.driver = setup_driver()
                else:
                    return "failed - max retries exceeded"

    def log_application_status(self, job_id, status):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = f"logs/job_application_{self.candidate_name}_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"

        try:
            os.makedirs("logs", exist_ok=True)
            file_exists = os.path.isfile(log_file)

            with open(log_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                if not file_exists:
                    writer.writerow(["jobId", "timestamp", "status"])
                writer.writerow([job_id, timestamp, status])
                f.flush()
            logging.info(f"Logged to CSV: \"{job_id}\",\"{timestamp}\",\"{status}\"")
        except Exception as e:
            logging.error(f"Failed to log to {log_file}: {e}")

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
                job_links.append(f"{self.lever_base_url}/{row.company}/{row.job_id}")

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

                self.driver.delete_all_cookies()
                self.driver.get("about:blank")
                logging.info("Browser reset for next job application.")

            except KeyboardInterrupt:
                logging.info("Application interrupted - saving state")
                self.save_session_state(job_link)
                self.driver.quit()
                return
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                self.log_application_status(job_link, f"failed - {str(e)}")
                continue

        self.driver.quit()
        logging.info("Job application process completed!")

class AshbyAutomation:
    def __init__(self):
        self.setup_logging()
        self.ashby_base_url = "https://jobs.ashbyhq.com"
        self.profile_yaml = self.select_profile()
        self.candidate_name = os.path.splitext(self.profile_yaml)[0]
        self.load_locators()
        self.credentials = self.load_config(f"credentials/{self.profile_yaml}")
        self.answers = self.load_answers("config/ashby_answers.csv")
        self.driver = setup_driver()
        self.wait = WebDriverWait(self.driver, 10)

    def setup_logging(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logging.basicConfig(
            filename="logs/ashby_terminal.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    def select_profile(self):
        config_dir = "credentials"
        yaml_files = [
            f for f in os.listdir(config_dir)
            if os.path.isfile(os.path.join(config_dir, f)) and f.lower().endswith(('.yaml', '.yml'))
        ]

        if not yaml_files:
            logging.error("No YAML files found in configuration directory.")
            raise FileNotFoundError("No YAML files found in configuration.")

        yaml_files.sort()
        print("Select a profile:")
        for idx, yaml_file in enumerate(yaml_files, 1):
            print(f"{idx} = {yaml_file}")

        while True:
            try:
                choice = input(f"Enter profile number (1-{len(yaml_files)}): ").strip()
                profile_num = int(choice)
                if 1 <= profile_num <= len(yaml_files):
                    selected_yaml = yaml_files[profile_num - 1]
                    logging.info(f"Selected profile: {selected_yaml}")
                    return selected_yaml
                else:
                    print(f"Please enter a number between 1 and {len(yaml_files)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def load_locators(self):
        try:
            with open("locators/ashby_locators.json", "r") as f:
                self.locators = json.load(f)
        except FileNotFoundError:
            logging.error("Locators file not found.")
            raise
        except json.JSONDecodeError:
            logging.error("Invalid JSON in locators file.")
            raise

    def load_config(self, file_location):
        try:
            with open(file_location, 'r') as stream:
                data = yaml.safe_load(stream)
        except FileNotFoundError:
            logging.error(f"Config file '{file_location}' not found.")
            raise
        except yaml.YAMLError as exc:
            logging.error(f"Error parsing YAML file: {exc}")
            raise

        required_fields = ["name", "email", "phone", "linkedin", "resume_path", "location"]
        credentials = {}

        for field in required_fields:
            if field not in data:
                logging.error(f"Required field '{field}' missing in YAML.")
                raise KeyError(f"Required field '{field}' missing in YAML.")
            credentials[field] = str(data[field])

        phone = credentials["phone"]
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        if not re.match(r"^\+?\d{8,15}$", cleaned_phone):
            logging.warning(f"Phone number format warning (continuing anyway): {phone}")

        credentials["github"] = str(data.get("github", ""))
        credentials["portfolio"] = str(data.get("portfolio", ""))
        credentials["work_status"] = str(data.get("work_status", ""))

        base_dir = os.path.dirname(os.path.abspath(__file__))
        resume_path = os.path.join(base_dir, credentials["resume_path"])
        if not os.path.isfile(resume_path):
            logging.error(f"Resume file not found at: {resume_path}")
            raise FileNotFoundError(f"Resume file not found at: {resume_path}")
        credentials["resume"] = resume_path

        return credentials

    def load_answers(self, file_path):
        answers = {}
        try:
            with open(file_path, mode="r", encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    question = row["Question"].strip().lower()
                    answers[question] = row["Answer"].strip()
            return answers
        except FileNotFoundError:
            logging.error(f"Answers file '{file_path}' not found.")
            raise

    def open_job_page(self, job_url):
        try:
            self.driver.get(job_url)
            logging.info(f"Opened job page: {job_url}")
            time.sleep(3)

            apply_selectors = self.locators["apply_selectors"]

            for selector in apply_selectors:
                try:
                    apply_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    apply_button.click()
                    logging.info("Apply button clicked successfully!")
                    time.sleep(5)
                    return
                except Exception as e:
                    logging.debug(f"Selector {selector} failed: {str(e)}")
                    continue

            raise Exception("Could not find apply button with any selector")
        except Exception as e:
            logging.error(f"Error in open_job_page: {str(e)}")
            raise

    def upload_resume(self):
        try:
            resume_path = self.credentials["resume"]

            if not resume_path:
                logging.error("No resume_path specified in YAML credentials")
                return False

            if not os.path.isabs(resume_path):
                resume_path = os.path.join(os.getcwd(), resume_path)

            if not os.path.exists(resume_path):
                logging.error(f"Resume file not found at: {resume_path}")
                return False

            logging.info(f"Attempting to upload resume from: {resume_path}")

            file_input = None
            selectors = self.locators["file_input_selectors"]

            for selector in selectors:
                try:
                    file_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except Exception:
                    continue

            if not file_input:
                logging.error("Could not find file input element")
                return False

            self.driver.execute_script("""
                arguments[0].style.display = 'block';
                arguments[0].style.visibility = 'visible';
                arguments[0].style.height = 'auto';
                arguments[0].style.width = 'auto';
                arguments[0].style.position = 'static';
                arguments[0].removeAttribute('hidden');
                arguments[0].removeAttribute('disabled');
            """, file_input)

            time.sleep(0.5)
            file_input.send_keys(resume_path)
            logging.info("Resume file sent to input element")

            try:
                WebDriverWait(self.driver, 15).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Upload complete')]")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='file-upload-success']")),
                        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'uploaded successfully')]")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "._success_1wnh2_1"))
                    )
                )
                logging.info("Resume upload confirmed by UI")
            except Exception as e:
                logging.warning(f"No explicit upload confirmation detected: {str(e)}")

            return True

        except Exception as e:
            logging.error(f"Error in resume upload: {str(e)}")
            return False

    def fill_application_form(self):
        try:
            logging.info("Filling out the application form...")

            fields = self.locators["form_fields"]

            for field_name, selectors in fields.items():
                value = self.credentials.get(field_name)
                if not value:
                    logging.warning(f"No value provided for mandatory field: {field_name}")
                    continue

                for selector in selectors:
                    try:
                        element = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        element.clear()
                        element.send_keys(value)
                        logging.info(f"Filled field {field_name} with value {value}")

                        if field_name == "location":
                            try:
                                suggestions = self.wait.until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.locators["location_suggestion"])))

                                desired_location = value.lower().strip()
                                location_found = False

                                for suggestion in suggestions:
                                    if suggestion.text.lower().strip() == desired_location:
                                        suggestion.click()
                                        logging.info(f"Selected location suggestion: {suggestion.text}")
                                        location_found = True
                                        break

                                if not location_found and suggestions:
                                    suggestions[0].click()
                                    logging.warning(f"Exact location match not found, selected first suggestion: {suggestions[0].text}")

                            except Exception as e:
                                logging.warning(f"Error selecting location suggestion: {str(e)}")
                                try:
                                    element.send_keys(Keys.ARROW_DOWN)
                                    element.send_keys(Keys.RETURN)
                                    logging.info("Selected location using keyboard navigation")
                                except Exception as fallback_e:
                                    logging.error(f"Failed to select location with fallback method: {str(fallback_e)}")
                        break
                    except Exception as e:
                        logging.warning(f"Error filling field {field_name} with selector {selector}: {str(e)}")
                        continue

            linkedin_value = self.credentials.get("linkedin")
            if linkedin_value:
                try:
                    linkedin_label = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'linkedin')]"))
                    )
                    linkedin_input = linkedin_label.find_element(By.XPATH, ".//following-sibling::input")
                    linkedin_input.clear()
                    linkedin_input.send_keys(linkedin_value)
                    logging.info("Filled LinkedIn field")
                except Exception as e:
                    logging.warning(f"LinkedIn field not found or failed to fill: {str(e)}")

            self.fill_qa_section()

            logging.info("Form filled successfully!")
            time.sleep(1)

        except Exception as e:
            logging.error(f"Error filling application form: {str(e)}")
            raise

    def fill_qa_section(self):
        def safe_strip(value):
            return str(value).strip() if pd.notna(value) else ""

        try:
            logging.info("Filling out the Q&A section...")

            if not self.answers:
                logging.info("No Q&A data to fill.")
                return

            try:
                form_container = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ashby-application-form-container"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", form_container)
                time.sleep(0.5)
            except:
                logging.warning("Could not locate form container")

            form_questions = self.get_form_questions()
            if not form_questions:
                logging.warning("No Q&A questions found in the form. Skipping Q&A section.")
                return

            for question, answer in self.answers.items():
                question = safe_strip(question)
                answer = safe_strip(answer)

                if not question:
                    logging.warning("Empty question found in CSV, skipping.")
                    continue

                logging.info(f"Processing question: '{question}'")

                matched_question, score = self.fuzzy_match_question(question, form_questions, threshold=80)
                if not matched_question:
                    logging.warning(f"No match found for question: '{question}' (best score: {score})")
                    continue
                logging.info(f"Matched CSV question '{question}' to form question '{matched_question}' (score: {score})")

                question_container = None
                escaped_question = self.escape_xpath_text(matched_question.lower())

                try:
                    question_container = self.wait.until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            f"//div[contains(@class, 'ashby-application-form-field-entry') and .//label[contains(normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')), {escaped_question})]]"
                        ))
                    )
                    self._highlight_element(question_container, "yellow")
                except Exception as e:
                    logging.debug(f"Primary XPath failed for '{matched_question}': {str(e)}")

                if not question_container:
                    for selector_template in self.locators["qa_selectors"]:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector_template)
                            for element in elements:
                                try:
                                    label = element.find_element(By.CSS_SELECTOR, "label.ashby-application-form-question-title")
                                    if fuzz.token_sort_ratio(matched_question.lower(), label.text.lower()) >= 80:
                                        question_container = element
                                        self._highlight_element(question_container, "yellow")
                                        logging.info(f"Found question '{matched_question}' using selector: {selector_template}")
                                        break
                                except:
                                    continue
                            if question_container:
                                break
                        except:
                            continue

                if not question_container:
                    logging.warning(f"Could not locate question: '{matched_question}'")
                    continue

                try:
                    container_html = question_container.get_attribute("outerHTML")[:500]
                    logging.debug(f"Question container HTML for '{matched_question}': {container_html}")

                    try:
                        answer_field = question_container.find_element(
                            By.XPATH, ".//input[not(@type='radio' or @type='checkbox')] | .//textarea")
                        answer_field.clear()
                        answer_field.send_keys(answer)
                        logging.info(f"Filled text input for '{matched_question}' with '{answer}'")
                        continue
                    except:
                        pass

                    try:
                        select = Select(question_container.find_element(By.XPATH, ".//select[not(@multiple)]"))
                        select.select_by_visible_text(answer)
                        logging.info(f"Selected dropdown option for '{matched_question}' with '{answer}'")
                        continue
                    except:
                        pass

                    try:
                        select = Select(question_container.find_element(By.XPATH, ".//select[@multiple]"))
                        select.select_by_visible_text(answer)
                        logging.info(f"Selected multi-select option for '{matched_question}' with '{answer}'")
                        continue
                    except:
                        pass

                    try:
                        radio = question_container.find_element(
                            By.XPATH, f".//input[@type='radio' and following-sibling::*[contains(normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')), '{answer.lower()}')]]")
                        self.driver.execute_script("arguments[0].click();", radio)
                        logging.info(f"Selected radio button for '{matched_question}' with '{answer}'")
                        continue
                    except:
                        pass

                    try:
                        button = question_container.find_element(
                            By.XPATH, f".//button[contains(normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')), '{answer.lower()}')]")
                        self.driver.execute_script("arguments[0].click();", button)
                        logging.info(f"Clicked button for '{matched_question}' with '{answer}'")
                        continue
                    except:
                        pass

                    try:
                        checkbox = question_container.find_element(
                            By.XPATH, f".//input[@type='checkbox' and @name='{answer}']")
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        logging.info(f"Checked checkbox for '{matched_question}' with '{answer}'")
                        continue
                    except:
                        pass

                    logging.warning(f"Could not determine answer field type for question: '{matched_question}'")

                except Exception as e:
                    logging.warning(f"Failed to answer question '{matched_question}': {str(e)}")

            logging.info("Q&A section filled successfully!")

        except Exception as e:
            logging.error(f"Error filling Q&A section: {str(e)}")
            raise

    def escape_xpath_text(self, text):
        """Escape special characters in XPath text to prevent syntax errors."""
        if "'" in text:
            parts = text.split("'")
            return "concat(" + ", '\"', ".join(f"'{part}'" for part in parts) + ")"
        return f"'{text}'"

    def get_form_questions(self):
        """Extract Q&A questions, excluding personal detail fields."""
        try:
            question_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "div._fieldEntry_hkyf8_29 label._heading_101oc_53._label_hkyf8_43.ashby-application-form-question-title"
            )
            exclude_keywords = ['name', 'email', 'phone', 'location', 'linkedin', 'resume']
            questions = [
                elem.text.strip() for elem in question_elements
                if elem.text.strip() and not any(keyword in elem.text.lower() for keyword in exclude_keywords)
            ]
            logging.info(f"Form Q&A questions found: {questions}")
            return questions
        except Exception as e:
            logging.warning(f"Could not extract form questions: {str(e)}")
            return []

    def fuzzy_match_question(self, csv_question, form_questions, threshold=80):
        """Find the best matching form question with at least 80% similarity, avoiding personal fields."""
        csv_question_clean = csv_question.lower().split('?.')[0].strip()
        best_match = None
        best_score = 0
        for form_question in form_questions:
            partial_score = fuzz.partial_ratio(csv_question_clean, form_question.lower())
            token_score = fuzz.token_sort_ratio(csv_question_clean, form_question.lower())
            combined_score = (partial_score * 0.4 + token_score * 0.6)
            if (combined_score > best_score and combined_score >= threshold and
                not any(keyword in form_question.lower() for keyword in ['location', 'email', 'name', 'phone', 'linkedin', 'resume'])):
                best_score = combined_score
                best_match = form_question
        logging.debug(f"Fuzzy match for '{csv_question}': Best match='{best_match}', Score={best_score}")
        return best_match, best_score

    def _wait_for_required_fields_to_be_filled(self):
        try:
            missing_fields = []

            while True:
                missing_fields.clear()

               
                required_fields = self.driver.find_elements(By.XPATH, "//*[@required]")
                for field in required_fields:
                    try:
                        field_type = field.get_attribute("type")
                        field_value = field.get_attribute("value")
                        field_name = field.get_attribute("name") or field.get_attribute("id") or "Unnamed Field"
                        logging.debug(f"Checking required field: type={field_type}, value={field_value}, name={field_name}")

                        if field_name == "_systemfield_resume":
                            continue

                        if field_type in ["radio", "checkbox"]:
                            if not field.is_selected():
                                missing_fields.append(field)
                                logging.info(f"Required radio/checkbox not selected: {field_name}")
                        elif field_value in [None, ""]:
                            missing_fields.append(field)
                            logging.info(f"Required field not filled: {field_name}")
                    except Exception as e:
                        logging.warning(f"Error checking required field: {str(e)}")
                        continue

                
                required_labels = self.driver.find_elements(By.XPATH, "//label[contains(@class, '_required_')]")
                for label in required_labels:
                    try:
                        for_attr = label.get_attribute("for")
                        if not for_attr:
                            continue

                       
                        radio_buttons = self.driver.find_elements(By.XPATH, f"//input[@type='radio' and contains(@id, '{for_attr}')]")
                        if radio_buttons:
                            if not any(rb.is_selected() for rb in radio_buttons):
                                missing_fields.append(label)
                                logging.info(f"Required radio group not answered: {label.text.strip()}")
                            continue

                       
                        checkbox_buttons = self.driver.find_elements(By.XPATH, f"//input[@type='checkbox' and contains(@id, '{for_attr}')]")
                        if checkbox_buttons:
                            if not any(cb.is_selected() for cb in checkbox_buttons):
                                missing_fields.append(label)
                                logging.info(f"Required checkbox group not answered: {label.text.strip()}")
                            continue

                    except Exception as e:
                        logging.warning(f"Error checking required group by label: {str(e)}")
                        continue

                if not missing_fields:
                    logging.info("All required fields are filled.")
                    return True

                missing_field_names = [
                    field.text.strip() if hasattr(field, 'text') and field.text.strip() else field.get_attribute("name") or field.get_attribute("id") or "Unnamed Field"
                    for field in missing_fields
                ]
                logging.info(f"Waiting for {len(missing_fields)} required fields to be filled: {missing_field_names}")
                time.sleep(2)

        except Exception as e:
            logging.error(f"Error while waiting for required fields to be filled: {str(e)}")
            return False

    def _highlight_element(self, element, color="yellow"):
        """Highlights (blinks) a Selenium WebElement."""
        driver = element._parent

        def apply_style(s):
            driver.execute_script("arguments[0].setAttribute('style', arguments[1]);",
                                  element, s)

        original_style = element.get_attribute('style')
        apply_style(f"border: 2px solid {color}; background-color: {color};")
        time.sleep(0.3)
        apply_style(original_style)

    def _find_submit_button(self):

        with open('locators/ashby_locators.json', 'r') as file:
            locators = json.load(file)
            
        submit_selectors = locators.get("submit_selectors", [])

        for selector in submit_selectors:
            try:
                button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if button.is_displayed():
                    logging.info(f"Found submit button using selector: {selector}")
                    self._highlight_element(button, "green")
                    return button
            except Exception as e:
                logging.debug(f"Selector failed: {selector} - {str(e)}")

        logging.error("Could not locate submit button using any known selectors")
        return None


    def _click_submit_button(self, button, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.5 + random.random())

                if attempt == 0:
                    button.click()
                    logging.info("Clicked submit button normally")
                elif attempt == 1:
                    self.driver.execute_script("arguments[0].click();", button)
                    logging.info("Used JavaScript click")
                else:
                    self.driver.execute_script("""
                        arguments[0].style.display = 'block';
                        arguments[0].style.visibility = 'visible';
                        arguments[0].style.opacity = 1;
                        arguments[0].click();
                    """, button)
                    logging.info("Used forced visibility click")

                time.sleep(2 + random.random())

                try:
                    button.is_displayed()
                    logging.debug(f"Still on same page after click attempt {attempt + 1}")
                except:
                    logging.info("Page changed after click - assuming submission started")
                    return True

            except Exception as e:
                logging.warning(f"Submit click attempt {attempt + 1} failed: {str(e)}")
                time.sleep(1 + random.random())

        return False

    def _verify_submission(self, timeout=20):
        confirmation_indicators = self.locators["confirmation_indicators"]
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(*[getattr(EC, ind["method"])((ind["by"], ind["value"])) for ind in confirmation_indicators])
            )
            logging.info("Clear submission confirmation detected")
            return True
        except Exception as e:
            logging.warning(f"Error during submission verification: {str(e)}")
            current_url = self.driver.current_url.lower()
            if not ("apply" in current_url or "form" in current_url):
                logging.info("URL suggests we left application page - assuming success")
                return True
            return False

    def submit_application(self):
        try:
            logging.info("Starting submission process...")

            if not self._wait_for_required_fields_to_be_filled():
                logging.error("Required fields not filled before submission")
               
                return False

            submit_button = self._find_submit_button()
            if not submit_button:
                logging.error("Could not locate submit button")
               
                return False

            if not self._click_submit_button(submit_button):
                logging.error("Failed to click submit button")
              
                return False

            submission_verified = self._verify_submission()

            if submission_verified:
                logging.info("Application submitted successfully!")
                
                return True
            else:
                logging.warning("Submission confirmation not clearly detected")
                
                return True

        except Exception as e:
            logging.error(f"Unexpected error during submission: {str(e)}")
           
            return False

    def log_application_status(self, status):
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        log_filename = f"logs/ashby_log_{current_date}.csv"

        

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        candidate_name = self.credentials.get("name", "Unknown")

        log_entry = f"[{timestamp}], {candidate_name}, {status}, {self.job_url}\n"

        try:
            os.makedirs("logs", exist_ok=True)
            logging.info(f"Log directory ensured: {os.path.abspath('logs')}")

            with open(log_filename, mode="a", newline="", encoding='utf-8') as file:
                print("this is printing")
                file.write(log_entry)
            logging.info(f"Log entry written to {log_filename}")
        except Exception as e:
            logging.error(f"Failed to write log entry: {str(e)}")

   
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
            if str(row.platform).lower() == "ashby":
                job_links.append(f"{self.ashby_base_url}/{row.company}/{row.job_id}")

        if not job_links:
            logging.error("No Ashby job links found in the CSV file.")
            return

        for job_link in job_links:
            self.job_url = job_link  
            logging.info(f"Processing job: {job_link}")

            try:
                self.open_job_page(job_link)
                self.upload_resume()
                self.fill_application_form()

              
                if self.submit_application():
                    self.log_application_status("Success")
                else:
                    self.log_application_status("Failed")

            except KeyboardInterrupt:
                logging.info("Application interrupted - saving state")
                self.log_application_status("Interrupted")
                self.driver.quit()
                return
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                self.log_application_status(f"Error: {str(e)}")
                continue

        self.driver.quit()
        logging.info("Job application process completed!")


def main():
    print("Select a project to run:")
    print("1. Greenhouse")
    print("2. Jobvite")
    print("3. Lever")
    print("4. Ashby")
    print("0. Exit")

    choice = input("Enter the number of your choice: ").strip()

    if choice == "1":
        greenhouse_automation = GreenhouseAutomation()
        greenhouse_automation.run()
    elif choice == "2":
        jobvite_automation = JobviteAutomation()
        jobvite_automation.run()
    elif choice == "3":
        lever_automation = LeverAutomation()
        lever_automation.run()
    elif choice == "4":
        ashby_automation = AshbyAutomation()
        ashby_automation.run()
    elif choice == "0":
        print("Exiting the program. Thank you for using the application!")
        exit(0)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
