# JobPortalApp 
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
## Technologies Used
* Backend: Django REST Framework (DRF)
* Databases: MySQL

=> Deploy to PythonAnywhere [Link](https://tdmtien.pythonanywhere.com/ )
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
