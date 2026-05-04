Metroline Driver Log System

## Key Highlights

* Built a SOC-style monitoring dashboard for transport operations
* Implemented role-based access control (Driver / Supervisor / Manager)
* Designed a digital replica of real-world Metroline log cards
* Developed backend logic for route and log management using Flask
* Structured project with production-style architecture (templates, static, database separation)

---

A SOC-style operational monitoring dashboard for managing driver logs, routes, and compliance visibility.

---

## Overview

This system digitises traditional Metroline paper log cards into a structured web application.

This project demonstrates backend development, system design, and operational monitoring concepts relevant to cybersecurity and SOC analyst roles.

It allows:

* Drivers to submit logs
* Supervisors to monitor activity
* Managers to view operational insights

---

## Features

* Role-based access (Driver / Supervisor / Manager)
* Digital driver log card (paper replica)
* Time tracking and log submission

### SOC-style dashboard includes:

* Total routes

* Total logs

* Daily activity

* Recent logs

* Route activity monitoring

* Route management system

* Metroline-inspired UI (dark operational theme)

---

## Tech Stack

* **Backend:** Flask (Python)
* **Database:** SQLite
* **Frontend:** HTML, CSS (custom UI)
* **Version Control:** Git & GitHub

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Z-a-d-e-1/driver-log-system.git
cd driver-log-system
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install flask python-dotenv
```

### 4. Set environment variables

Create `.env` file:

```text
SECRET_KEY=your-secret-key
```

### 5. Run the application

```bash
python app.py
```

Then open:

```
http://127.0.0.1:5000
```

---

## ## 🎥 System Overview

A real-world inspired transport operations platform built with Flask, simulating a Metroline-style driver log and monitoring system.

Key capabilities:

- Role-based authentication (Driver / Supervisor / Manager)
- Digital log card submission system
- SOC-style monitoring dashboard
- Route and operational visibility
- Compliance tracking logic (driving time / break rules)

## Screenshots

### Landing Page
<p align="center">
  <img src="screenshots/landing.png" width="700">
</p>

### Login
<p align="center">
  <img src="screenshots/login.jpg" width="400">
</p>

### Dashboard
<p align="center">
  <img src="screenshots/dashboard.jpg" width="800">
</p>

### Log Card
<p align="center">
  <img src="screenshots/log-card.jpg" width="700">
</p>


---

## Security

* Environment variables used for sensitive data
* Database excluded from version control
* GitHub email privacy protection enabled

---

## Future Improvements

* Break compliance detection (5h30 / 45min rule)
* Real-time alerts (red / amber / green status)
* PostgreSQL migration
* Deployment to cloud (Render / Railway)

---

## Author

**Tracy Mckoy**
Aspiring SOC Analyst | Cybersecurity Student
GitHub: https://github.com/Z-a-d-e-1
