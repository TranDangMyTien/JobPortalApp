from jobs.models import (JobApplication, RecruitmentPost, Employer, Applicant, EmploymentType,
                         Career, Comment, Rating, Like,
                         )
from django.db.models import Count, Q, Avg
from datetime import datetime
from django.db.models.functions import ExtractQuarter, ExtractYear, TruncMonth


# Theo đề bài: Viết câu truy vấn đếm số đơn ứng tuyển của sinh viên theo nghề qua các quý và năm
def count_job_application_quarter_career():
    queryset = JobApplication.objects.filter(is_student=True) \
        .annotate(quarter=ExtractQuarter('date'), year=ExtractYear('date')) \
        .values('recruitment__career__name', 'quarter', 'year') \
        .annotate(total_applications=Count('id')).order_by('total_applications', 'year', 'quarter')

    return queryset


# Viết câu truy vấn đếm số lượng đơn xin việc (JobApplication) là giới tính nữ mỗi bài đăng tuyển việc làm (RecruitmentPost)
# Kèm theo tổng số đơn xin việc của mỗi bài tuyển dụng
def recruitment_posts_with_female_applicants():
    return RecruitmentPost.objects.annotate(
        num_female_applicants=Count('jobapplication', filter=Q(jobapplication__applicant__user__gender=1)),
        # Giới tính nữ trong choices là 1
        total_applications=Count('id'),
    ).values('id', 'title', 'num_female_applicants', 'total_applications')


# Tìm các bài đăng tuyển việc làm trên mức lương người dùng nhập
def search_salary_recruiment_post(salary):
    return RecruitmentPost.objects.filter(salary__gte=salary).order_by('-salary')



# Đếm số lượng bài tuyển dụng của mỗi nhà tuyển dụng
def count_recruitment_posts_per_employer():
    return Employer.objects.annotate(num_recruitment_posts=Count('recruitmentpost'))


# Đếm số lượng đơn xin việc của mỗi ứng viên
def count_job_applications_per_applicant():
    return Applicant.objects.annotate(num_job_applications=Count('jobapplication'))


# Đếm số lượng bài tuyển dụng theo loại công việc
def count_recruitment_posts_per_employment_type():
    return EmploymentType.objects.annotate(num_recruitment_posts=Count('recruitmentpost'))


# Đếm số lượng bài tuyển dụng theo ngành nghề
def count_recruitment_posts_per_career():
    return Career.objects.annotate(num_recruitment_posts=Count('recruitmentpost'))

# Đếm số lượng đơn xin việc là giới tính nữ
def count_female_job_applications():
    return JobApplication.objects.filter(applicant__user__gender=1).count()

# Đếm số lượng bài tuyển dụng là giới tính nữ
def count_recruitment_posts_with_female_employees():
    return RecruitmentPost.objects.filter(gender=1).count()

# Đếm số lượng đơn xin việc theo tháng
def count_job_applications_per_month():
    return JobApplication.objects.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total_applications=Count('id')
    )

# Đếm số bài tuyển dụng theo nghề
def count_recruitment_posts_by_career():
    return RecruitmentPost.objects.values('career__name').annotate(total_posts=Count('id'))

# Đếm số lượng bài đăng tuyển dụng theo vị trí địa lý
def count_recruitment_posts_by_location():
    recruitment_posts_by_location = RecruitmentPost.objects.values('location').annotate(
        total=Count('id')
    ).order_by('-total')

    return recruitment_posts_by_location

# Đếm số lượng bài đăng tuyển dụng theo người đăng tuyển dụng
def count_recruitment_posts_by_employer():
    recruitment_posts_by_employer = RecruitmentPost.objects.values('employer__companyName').annotate(
        total=Count('id')
    ).order_by('-total')

    return recruitment_posts_by_employer

# Tính tổng số lượt comment trung bình mỗi bài đăng tuyển dụng
def average_comments_per_recruitment_post():
    average_comments = Comment.objects.values('interaction__recruitment').annotate(
        average_comments=Avg('id')
    ).aggregate(
        overall_average=Avg('average_comments')
    )

    return average_comments


# Tính tổng số lượt rating trung bình mỗi bài đăng tuyển dụng
def average_ratings_per_recruitment_post():
    average_ratings = Rating.objects.values('interaction__recruitment').annotate(
        average_ratings=Avg('rating')
    ).aggregate(
        overall_average=Avg('average_ratings')
    )

    return average_ratings

# Tính tổng số lượt like trung bình mỗi bài đăng tuyển dụng
def average_likes_per_recruitment_post():
    average_likes = Like.objects.values('interaction__recruitment').annotate(
        average_likes=Avg('id')
    ).aggregate(
        overall_average=Avg('average_likes')
    )

    return average_likes

# Đếm số lượng bài đăng tuyển dụng có mức lương cao hơn 10 triệu VND
def count_recruitment_posts_with_high_salary():
    recruitment_posts_with_high_salary = RecruitmentPost.objects.filter(
        salary__gt=10000000
    ).count()

    return recruitment_posts_with_high_salary

# Đếm số lượng ứng viên có mức lương mong đợi trên 15 triệu VND
def count_applicants_with_high_salary_expectation():
    applicants_with_high_salary_expectation = Applicant.objects.filter(
        salary_expectation__gt=15000000
    ).count()

    return applicants_with_high_salary_expectation




# Đếm số lượng bài đăng tuyển dụng có vị trí là "Nhân viên kinh doanh"
def count_recruitment_posts_with_sales_position():
    recruitment_posts_with_sales_position = RecruitmentPost.objects.filter(
        position__icontains='nhân viên kinh doanh'
    ).count()

    return recruitment_posts_with_sales_position

