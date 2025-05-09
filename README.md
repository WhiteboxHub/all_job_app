# Job Application Automation

This project automates the job application process for three platforms: Greenhouse, Jobvite, and Lever. It uses Selenium WebDriver to interact with web elements, fill out forms, and submit applications.

## Features

- **Multi-Platform Support**: Automates applications for Greenhouse, Jobvite, and Lever.
- **User Configuration**: Loads user credentials and resumes from YAML and CSV files.
- **Form Filling**: Automatically fills out application forms using predefined answers.
- **Error Handling**: Robust error handling and logging for troubleshooting.
- **Session Management**: Saves and resumes application sessions.

## Prerequisites

- Python 3.6 or higher
- Selenium WebDriver
- ChromeDriver
- Required Python packages: `selenium`, `undetected_chromedriver`, `pyyaml`, `pandas`, `fuzzywuzzy`, `webdriver_manager`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/WhiteboxHub/all_job_app.git
   cd all_job_app
   ```
2. Create and activate a virtual environment:

   macOS/Linux:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   Windows:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **User Credentials**: Place your user credentials in YAML files in the `credentials` directory.
2. **Job Links**: Add job links to the `jobs/linkedin_jobs.csv` file.
3. **Answers**: Provide answers to common application questions in the `config/greenhouse_answers.csv`, `config/jobvite_answers.csv`, and `config/lever_answers.csv` files.
4. **Locators**: Define CSS selectors and XPath expressions for form elements in the `locators` directory.
5. **Resume**: add all the required resumes and in required format  in the `resume` directory.

## Usage

Run the main script to start the automation process:

```bash
python main.py
```

Follow the on-screen instructions to select a user profile and platform.

## Project Structure

- `credentials/`: Contains user credential files in YAML format.
- `config/`: Contains CSV files with answers to common application questions.
- `jobs/`: Contains CSV files with job links.
- `locators/`: Contains JSON files with CSS selectors and XPath expressions for form elements for each platform.
- `logs/`: Contains log files for troubleshooting.
- `resume/`: Contains all the resumes files.
- `main.py`: The main script to run the automation process.

#### - Made with ❤️ by Whitebox developers
