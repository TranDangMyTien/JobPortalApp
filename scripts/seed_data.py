import os
import sys
import django
import random
from django.utils import timezone
from datetime import timedelta

# Thêm thư mục gốc của dự án vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Thiết lập biến môi trường DJANGO_SETTINGS_MODULE
os.environ['DJANGO_SETTINGS_MODULE'] = 'jobPortal.settings'

# Thiết lập Django
django.setup()

# Kiểm tra nếu Django đã được thiết lập đúng cách
print("Django setup is working correctly.")

from jobs.models import *


def create_sample_data():
    # Tạo Areas
    areas = ['District 1 - HCM', 'District 2 - HCM', 'District 3 - HCM', 'District 4 - HCM', 'District 5 - HCM',
             'District 6 - HCM', 'District 7 - HCM', 'District 8 - HCM', 'District 9 - HCM', 'District 10 - HCM',
             'District 11 - HCM', 'District 12 - HCM', 'Tan Binh District - HCM', 'Binh Tan District - HCM',
             'Go Vap District - HCM', 'Binh Thanh District - HCM', 'Thu Duc District - HCM', 'Nha Be District - HCM',
             'Cu Chi District - HCM', 'Can Gio District - HCM', 'Hoc Mon District - HCM', 'Binh Chanh District - HCM',
             'Tan Phu District - HCM']
    area_objects = []
    for area in areas:
        obj, created = Area.objects.get_or_create(name=area)
        area_objects.append(obj)

    # Tạo Careers
    careers = [
        'Programmer', 'Designer', 'Marketing Specialist', 'Student',
        'Receptionist', 'Restaurant Server', 'Content Creator',
        'Social Media Manager', 'Data Entry', 'Editor',
        'Manager', 'Teaching Assistant', 'Teacher', 'Technician',
        'Marketing', 'Architect', 'Fashion Designer', 'Banker',
        'Pharmacist', 'Administration', 'Human Resources',
        'Graphic Designer', 'Secretary', 'Construction Supervisor',
        'Customer Service', 'Sales Consultant', 'Business Development',
        'Accountant', 'Project Manager', 'Software Engineer',
        'Legal Advisor', 'Product Manager', 'Consultant',
        'Supply Chain Manager', 'Financial Analyst',
        'Network Engineer', 'Data Scientist', 'Cybersecurity Specialist',
        'Web Developer', 'IT Support Specialist', 'Digital Marketer',
        'UX/UI Designer', 'Public Relations Manager', 'Content Strategist',
        'Operations Manager', 'Quality Assurance Engineer',
        'Event Coordinator', 'HR Consultant', 'Translator',
        'Logistics Coordinator', 'Healthcare Administrator',
        'Clinical Researcher', 'Copywriter'
    ]
    career_objects = []
    for career in careers:
        obj, created = Career.objects.get_or_create(name=career)
        career_objects.append(obj)


    # Tạo Skills
    skills = ['English', 'Chinese', 'Python', 'Research', 'Github', 'Java', 'Teamwork', 'Time management',
              'Problem-solving', 'Logical thinking', 'Algorithmic thinking', 'Communication', 'Self-learning',
              'Creativity', 'Patience', 'RESTful API', 'C#', 'C++', 'C', 'HTML', 'JavaScript', 'SQL', 'Leadership',
              'Adaptability', 'Critical thinking', 'Project management', 'Attention to detail']
    skill_objects = []
    for skill in skills:
        obj, created = Skill.objects.get_or_create(name=skill)
        skill_objects.append(obj)


    # Tạo Employment Types
    employment_types = ['Full-time', 'Part-time', 'Internship', 'On-site', 'Remote/WFH', 'Hybrid']
    for employment_type in employment_types:
        EmploymentType.objects.get_or_create(type=employment_type)

    # Tạo Status
    role = ['Pending', 'Accepted', 'Rejected', 'Under Review', 'Interviewed']
    for status in role:
        Status.objects.get_or_create(role=status)



    # Tạo Users
    users = [
        {'username': 'admin', 'email': 'admin@gmail.com', 'password': 'm1234567890', 'is_staff': True},
        {'username': 'admin1', 'email': 'admin1@gmail.com', 'password': 'm1234567890', 'is_staff': True},
        {'username': 'applicant1', 'email': 'applicant1@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 0},
        {'username': 'applicant2', 'email': 'applicant2@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 1},
        {'username': 'applicant3', 'email': 'applicant3@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 2},
        {'username': 'applicant4', 'email': 'applicant4@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 0},
        {'username': 'applicant5', 'email': 'applicant5@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 3},
        {'username': 'applicant6', 'email': 'applicant6@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 1},
        {'username': 'applicant7', 'email': 'applicant7@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 1},
        {'username': 'applicant8', 'email': 'applicant8@gmail.com', 'password': 'm1234567890',
         'is_employer': False, 'gender': 0},
        {'username': 'employer1', 'email': 'employer1@@gmail.com', 'password': 'm1234567890',
         'is_employer': True, 'gender': 0},
        {'username': 'employer2', 'email': 'employer2@@gmail.com', 'password': 'm1234567890',
         'is_employer': True, 'gender': 0},
        {'username': 'employer3', 'email': 'employer3@@gmail.com', 'password': 'm1234567890',
         'is_employer': True, 'gender': 1},
        {'username': 'employer4', 'email': 'employer4@@gmail.com', 'password': 'm1234567890',
         'is_employer': True, 'gender': 3},
        {'username': 'employer5', 'email': 'employer5@@gmail.com', 'password': 'm1234567890',
         'is_employer': True, 'gender': 1},

    ]

    # Map some sample company data to be used when creating employers
    company_data = [
        {'companyName': 'Tech Solutions Ltd', 'address': '123 Tech Street', 'information': 'A leading tech company.',
         'position': 'HR Manager', 'company_website': 'https://techsolutions.com', 'company_type': 0},
        {'companyName': 'Design Pros', 'address': '45 Design Avenue', 'information': 'Creative design agency.',
         'position': 'Recruiter', 'company_website': 'https://designpros.com', 'company_type': 2},
        {'companyName': 'Market Masters', 'address': '78 Market Lane', 'information': 'Marketing and consulting firm.',
         'position': 'HR Executive', 'company_website': 'https://marketmasters.com', 'company_type': 3},
        {'companyName': 'BuildCon', 'address': '90 Build Blvd', 'information': 'Construction and development company.',
         'position': 'Talent Acquisition', 'company_website': 'https://buildcon.com', 'company_type': 1},
        {'companyName': 'HealthFirst', 'address': '100 Wellness Way', 'information': 'Healthcare services provider.',
         'position': 'HR Specialist', 'company_website': 'https://healthfirst.com', 'company_type': 2},
    ]

    for index, user_data in enumerate(users):
        user = None
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                is_employer=user_data.get('is_employer', False),
                gender=user_data.get('gender', None)
            )
            if user_data.get('is_staff', False):
                user.is_staff = True
                user.save()

        # Tạo Employer chỉ khi user không phải là None
        if user and user_data.get('is_employer', False):
            if index - len(users) + len(company_data) >= 0:  # Đảm bảo chỉ số không vượt quá giới hạn
                data = company_data[index - len(users) + len(company_data)]
                Employer.objects.get_or_create(
                    user=user,
                    companyName=data['companyName'],
                    address=data['address'],
                    information=data['information'],
                    position=data['position'],
                    company_website=data['company_website'],
                    company_type=data['company_type']
                )
        # Tạo Applicant
        elif user:  # Đảm bảo user không phải là None
            applicant = Applicant.objects.get_or_create(
                user=user,
                position=random.choice(
                    ['Junior Developer', 'Data Analyst', 'Designer', 'Project Manager', 'Software Engineer',
                     'Marketing Specialist', 'Business Analyst', 'IT Support Specialist', 'Quality Assurance Engineer',
                     'Web Developer', 'Data Scientist', 'Digital Marketer', 'HR Specialist', 'Sales Consultant',
                     'Operations Manager', 'Network Engineer', 'UX/UI Designer', 'Content Creator', 'Graphic Designer',
                     'Product Manager', 'Social Media Manager', 'Financial Analyst', 'Customer Service Representative',
                     'System Administrator', 'Backend Developer', 'Frontend Developer']),
                salary_expectation=random.randint(300, 2000) * 1000,
                experience="This is a sample experience text.",
                career=random.choice(career_objects)
            )
            applicant.skills.set(random.sample(skill_objects, random.randint(1, 5)))
            applicant.areas.set(random.sample(area_objects, random.randint(1, 3)))
            applicant.save()

    # Danh sách các vị trí công việc
    job_positions = [
        'Software Engineer', 'Data Scientist', 'Product Manager', 'UX Designer',
        'Marketing Specialist', 'Business Analyst', 'Graphic Designer', 'Project Manager',
        'HR Specialist', 'Sales Representative'
    ]

    # Tạo RecruitmentPosts
    now = timezone.now()
    for i in range(20):
        position = random.choice(job_positions)
        employer = Employer.objects.order_by('?').first()
        area = random.choice(area_objects)
        career = random.choice(career_objects)
        employment_type = EmploymentType.objects.order_by('?').first()
        title = f'Recruitment position: {position}'
        description = f"Join our team at {employer.companyName} as a {career.name}. We are looking for talented individuals who have experience in {career.name}. {employer.information}."

        # Kiểm tra xem một mục với cùng title và employer đã tồn tại chưa
        if not RecruitmentPost.objects.filter(title=title, employer=employer).exists():
            RecruitmentPost.objects.create(
                title=title,
                description=description,
                employer=employer,
                career=career,
                area=area,
                employmenttype=employment_type,
                deadline=timezone.now() + timezone.timedelta(days=random.randint(30, 90)),
                quantity=random.randint(1, 10),
                gender=random.choice([0, 1, 2, 3]),
                location='Ho Chi Minh City',
                salary=random.randint(500, 5000) * 1000,
                position=position,
                reported=False,
                created_date=timezone.now(),
                updated_date=timezone.now()
            )

if __name__ == '__main__':
    create_sample_data()
    print("Sample data created successfully.")