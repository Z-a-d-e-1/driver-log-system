# Metroline Driver Log System

## Key Highlights

- Built a SOC-style monitoring dashboard for transport operations  
- Implemented role-based access control (Driver / Supervisor / Manager)  
- Designed a digital replica of real-world Metroline log cards  
- Developed backend logic for route and log management using Flask  
- Structured project using production-style architecture (templates, static, database separation)  

---

A SOC-style operational monitoring dashboard for managing driver logs, routes, and compliance visibility.

---

## Overview

This system digitises traditional Metroline paper log cards into a structured web application.

The project demonstrates:

- Backend development with Flask  
- System design and data modelling  
- Operational monitoring concepts aligned with SOC analyst workflows  

### User Roles

- **Drivers** → Submit logs  
- **Supervisors** → Monitor activity  
- **Managers** → View operational insights  

---

## Features

- Role-based access control (Driver / Supervisor / Manager)  
- Digital driver log card (paper replica)  
- Time tracking and structured log submission  
- Route management system  
- Metroline-inspired UI (dark operational theme)  

### SOC-Style Dashboard

- Total routes overview  
- Total logs tracking  
- Daily activity monitoring  
- Recent log submissions  
- Route activity insights  

---

## Tech Stack

- **Backend:** Flask (Python)  
- **Database:** SQLite  
- **Frontend:** HTML, CSS (custom UI)  
- **Version Control:** Git & GitHub  

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

## ## System Overview

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
