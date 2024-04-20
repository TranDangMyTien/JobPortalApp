from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from ckeditor.fields import RichTextField


# Create your models here.

# calss abstract
class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True )
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True  # Không tạo model dưới CSDL

GENDER_CHOICES = (
    (0, 'Male'),
    (1, 'Female'),
    (2, 'Both male and female'),
    (3, 'Gender unknown')
)

COMPANY_CHOICES = (
    (0, 'Công ty TNHH'),
    (1, 'Công ty Cổ phần'),
    (2, 'Công ty trách nhiệm hữu hạn một thành viên'),
    (3, 'Công ty tư nhân'),
    (4, 'Công ty liên doanh'),
    (5, 'Công ty tập đoàn')
)

class User(AbstractUser):
    avatar = CloudinaryField('avatar', null=True, blank=True)
    mobile = PhoneNumberField(region="VN", null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, null=True, blank=True)
    is_employer = models.BooleanField(default=False)
    is_applicant = models.BooleanField(default=False)
    class Meta:
        ordering = ['id']  # Sắp xếp theo thứ tự id tăng dần


# Nhà tuyển dụng
class Employer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Tên công ty tuyển dụng
    companyName = models.CharField(max_length=255)
    # Vị trí công ty
    address = models.CharField(max_length=255, null=True, blank=True)
    # Thông tin công ty
    information = models.TextField(null=True, blank=True)
    # Vị trí người tuyển dụng
    position = models.CharField(max_length=255, null=True, blank=True)
    # Website thông tin công ty, dùng URLField
    company_website = models.URLField()
    # Loại hình công ty (công ty TNHH, công ty cổ phần, v.v)
    company_type = models.IntegerField(choices=COMPANY_CHOICES, null=True, blank=True)
    # Ngành nghề hoạt động
    def __str__(self):
        return self.user.username
    class Meta:
        ordering = ['id']

# Người xin việc
class Applicant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Vị trí muốn ứng tuyển
    position = models.CharField(max_length=255, null=True, blank=True)
    # Các kỹ năng làm việc
    skills = models.ManyToManyField('Skill')
    # Khu vực muốn làm việc
    areas = models.ManyToManyField('Area')
    # Mức lương mong muốn
    salary_expectation = models.IntegerField()
    # Kinh nghiệm làm việc
    experience = models.TextField(null=True, blank=True)
    # cv của ứng viên
    cv = CloudinaryField('cv', null=True, blank=True)
    # Nghề nghiệp
    career = models.ForeignKey('Career', on_delete=models.RESTRICT, null=True, blank=True)
    def __str__(self):
        return self.user.username
    class Meta:
        ordering = ['id']


# Khu vực
class Area(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# Loại công việc
class EmploymentType(BaseModel):

    type = models.CharField(max_length=100, unique=True, null=True, blank=True)
    # full_time; part_time; internship
    def __str__(self):
        return self.type
    class Meta:
        ordering = ['id']

# Bài tuyển dụng
class RecruitmentPost(BaseModel):
    employer = models.ForeignKey(Employer, models.CASCADE)
    career = models.ForeignKey('Career', on_delete=models.PROTECT, null=True)
    employmenttype = models.ForeignKey(EmploymentType, on_delete=models.PROTECT, null=True)
    # Tiêu đề
    title = models.CharField(max_length=255)
    # Ngày hết hạn
    deadline = models.DateField()
    # Số nhân sự cần
    quantity = models.IntegerField()
    # Giới tính
    gender = models.IntegerField(choices=GENDER_CHOICES, default=0, null=True, blank=True)
    # Nơi làm việc
    location = models.CharField(max_length=255)
    # Mức lương
    salary = models.IntegerField()
    # Chức vụ
    position = models.CharField(max_length=255)
    # Mô tả công việc
    description = models.TextField(null=True, blank=True)
    # Yêu cầu kinh nghiệm
    experience = models.CharField(max_length=255)
    # Có bị báo cáo hay không
    reported = models.BooleanField(default=False, null=True, blank=True)
    def __str__(self):
        return self.title
    class Meta:
        unique_together = ('employer', 'title')
        ordering = ['-created_date', 'id']




# Đơn xin việc
class JobApplication(BaseModel):
    is_student = models.BooleanField(default=False, null=True)  # Thêm để thực hiện truy vấn theo bài
    date = models.DateTimeField(null=True)  # Thêm mới để thực hiện truy vấn theo bài
    recruitment = models.ForeignKey(RecruitmentPost, models.RESTRICT, null=True)
    applicant = models.ForeignKey(Applicant, models.RESTRICT, null=True)
    status = models.ForeignKey('Status', models.RESTRICT, null=True, default='Pending')
    coverLetter = RichTextField(null=True, blank=True)
    class Meta:
        unique_together = ('recruitment', 'applicant')
        ordering = ['created_date', 'id']
    def __str__(self):
        return self.recruitment.title + ", " + self.applicant.user.username + " apply"



class Status(BaseModel):
    # Pending; Accepted; Rejected
    role = models.CharField(max_length=255, unique=True, null=True, blank=True)
    def __str__(self):
        return self.role


class Skill(models.Model):
    name = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name



class Career(models.Model):
    name = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

# Tương tác
class Interaction(BaseModel):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, null=True, blank=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, null=True, blank=True)
    recruitment = models.ForeignKey(RecruitmentPost, on_delete=models.CASCADE, null=True )
    class Meta:
        abstract = True
    def __str__(self):
        return f'{self.applicant_id} - {self.employer_id} - {self.recruitment_id}'


class Comment(Interaction):
    content = models.CharField(max_length=255)

    def __str__(self):
        return self.content
    class Meta:
        ordering = ['id', ]

class Like(Interaction):
    class Meta:
        unique_together = [['applicant', 'recruitment'], ['employer', 'recruitment']]
        ordering = ['id', ]


class Rating(Interaction):
    rating = models.SmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate from 1 to 5"
    )
    class Meta:
        unique_together = [['applicant', 'recruitment'], ['employer', 'recruitment']]
        ordering = ['id',]

