# JobPortalApp 
<span><img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django logo" title="Django" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python logo" title="Python" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Canva-00C4CC?style=for-the-badge&logo=canva&logoColor=white" alt="Canva logo" title="Canva" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black" alt="Swagger logo" title="Swagger" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker logo" title="Docker" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/MySQL-00758F?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL logo" title="MySQL" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Heroku-430098?style=for-the-badge&logo=heroku&logoColor=white" alt="Heroku logo" title="Heroku" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Gmail Notifications-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Notification Gmail logo" title="Notification Gmail" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Stripe-008CDD?style=for-the-badge&logo=stripe&logoColor=white" alt="Stripe logo" title="Stripe" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis logo" title="Redis" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/WebSocket-000000?style=for-the-badge&logo=websocket&logoColor=white" alt="WebSocket logo" title="WebSocket" height="25" /></span>
&nbsp; 
<span><img src="https://img.shields.io/badge/Jazzmin-6F2DA8?style=for-the-badge&logo=python&logoColor=white" alt="Jazzmin logo" title="Jazzmin" height="25" /></span>
&nbsp;
<span><img src="https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" alt="Chart.js logo" title="Chart.js" height="25" /></span>
&nbsp;

***
## Overview
JobPortalApp, also known as **OU Job**, is a modern job search platform designed for students, job seekers, and employers. Inspired by TopCV, this platform offers comprehensive features to manage job postings, applications, and user interactions. JobPortalApp aims to facilitate job opportunities for students and job seekers, while providing employers with a powerful tool to find the best candidates. The platform is designed and developed by **Tran Dang My Tien**.
## Features
### User Roles 
- ***Applicant***: Apply for jobs, save favorites, review applications, and view suggested jobs. 
- **Employer**: Post job listings, review applications, manage applicants (default status: Pending), and search for candidates.
- ***Admin***: Approve employer registrations, manage the platform, and send email notifications.
### Key Functionalities
- ***Search and Interaction***: 
$\to$ Search jobs by criteria such as job type, newest listings, and most applied jobs.
$\to$ Like, rate, and comment on job postings.
- ***Registration and Authentication***:
$\to$ Default role for new users is Applicant; Employers require admin approval.
$\to$ Supports OAuth2 for secure login.
- ***Account Management***:
$\to$ Applicants and Employers can update personal information, manage their accounts, and delete them if necessary.
- ***System***:
$\to$ Analyze data from the database, use algorithms to make predictions. Display statistical reports and predictions on the admin page.

## Technologies Used
* Backend: Django REST Framework (DRF)
* Databases: MySQL
* CI/CD: Github, Jenkins, Ngrok 
* Chat real-time: WebSocket 
* Deployment and hosting: Docker, Heroku 
* Charts and data visualization: Chart.js
* Notifications: Gmail
* Payments: Stripe
* Support admin to manage the system: Jazzmin
=> Deploy to PythonAnywhere [Link](https://tdmtien.pythonanywhere.com/ )

## Admin pages
* Domain/myadmin/stats: Basic statistics.
* Domain/myadmin/search: Search for job postings.
* Domain/myadmin/job_market_stats: Detailed statistics of the whole system.
* Domain/myadmin/analysis-results: Analyze data using algorithms and make predictions.


## Getting Started
### Prerequisites
1. Python and pip installed
2. MySQL database setup
### Installation
1. Clone the repository:
``` git
git clone "https://github.com/TranDangMyTien/JobPortalApp"
cd JobPortalApp
```
2. Setup:

~ Navigate to the 'your_backend' directory and set up the virtual environment:
```python 
cd your_backend
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
~ ~ Install dependencies:
``` 
pip install -r requirements.txt
```
~ ~ ~ Apply migrations and start the Django server:
``` 
python manage.py migrate
python manage.py runserver
```
## Contact
For any inquiries or issues, please contact Tran Dang My Tien at [mytien.2682003@gmail.com](mytien.2682003@gmail.com)
