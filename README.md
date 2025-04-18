
# All Job Applications Automation

This project combines three separate job application automation scripts into one unified codebase:
- ✅ Greenhouse
- ✅ Lever
- ✅ Jobvite

Each script can still run independently, but now you can run them all from a single entry point.

---

## 📁 Project Structure

```
all_job_apps/
│
├── main.py                     # Central script to run all automations
├── requirements.txt            # Combined dependencies
│
├── greenhouse/                 # Greenhouse automation
│   └── (original files + run.py)
├── lever/                      # Lever automation
│   └── (original files + run.py)
├── jobvite/                    # Jobvite automation
│   └── (original files + run.py)
│
└── README.md                   # This file
```

---

## 🚀 How to Use

### 1. Clone the repository and install dependencies

```bash
git clone <repo-url>
cd all_job_apps
pip install -r requirements.txt
```

### 2. Run all automations at once

```bash
python main.py
```

### 3. Run individual automations

Each automation module (Greenhouse, Lever, Jobvite) has a `run.py` file.

```bash
python greenhouse/run.py
python lever/run.py
python jobvite/run.py
```

---

## 🛠️ Configuration

All user-specific and platform-specific files remain in their respective folders:
- `config/`, `credentials/`, `locators/`, `resume/`, `logs/` remain unchanged
- Use `answers.csv`, YAML credentials, and JSON locator files as before

---

## 📦 Dependencies

All dependencies from the three projects are combined in `requirements.txt`. Be sure to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🙌 Authors

Made with 💻 by combining automation logic from 3 projects.
