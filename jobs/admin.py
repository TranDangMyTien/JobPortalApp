from django.contrib import admin
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from jobs.models import (User, Employer, Applicant, Area, EmploymentType, RecruitmentPost, JobApplication, Status,
                         Skill,
                         Career, Comment, Rating, Like)
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
import cloudinary
from django.urls import path
from jobs import dao
from django.shortcuts import render
from django.contrib.auth.models import Permission  # Phần chứng thực


class JobApplicationForm(forms.ModelForm):
    coverLetter = forms.CharField(widget=CKEditorUploadingWidget)  # Để upload ảnh ở CKEditor

    class Meta:
        model = JobApplication
        fields = '__all__'


class JobApplicationAdmin(admin.ModelAdmin):
    form = JobApplicationForm
    list_display = ['id', 'recruitment', 'applicant', 'status', 'active', 'created_date']
    search_fields = ['id', 'created_date', 'status__role', 'recruitment__title', 'applicant__user__username']
#   'status__role' => lấy trường role ở bảng Status thông qua khóa ngoại status của bảng hiện tại JobApplication
#   'applicant__user__username' => Tương tự như vậy nhưng đi qua thêm 1 bảng trung gian nữa (User)


# Thiết kế lại form cho model User
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
    # Thiết kế chỉ cho tick vào 1 trường
    def clean(self):
        cleaned_data = super().clean()
        option1 = cleaned_data.get('is_employer')
        option2 = cleaned_data.get('is_applicant')
        if option1 and option2:
            raise forms.ValidationError("Can only be selected as employer or applicant.")

        if not option1 and not option2:
            raise forms.ValidationError("Must choose whether to be the employer or the applicant.")

        return cleaned_data


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'mobile', 'email', 'gender', 'is_superuser', 'is_employer', 'is_applicant']
    search_fields = ['id', 'mobile']
    readonly_fields = ['is_superuser']  # Trường is_superuser chỉ cho đọc không cho chỉnh
    form = UserForm  # Ghi đè lại form mặc định (form mình tự tạo ghi đè lên)

    # Thiết kế để khi lick vào link url của ảnh thì có thể truy cập vào ảnh
    def avatar(self, user):
        if user.avatar:
            if type(user.image) is cloudinary.CloudinaryResource:
                return mark_safe(
                    "<img src='{img_url}' alt='{alt}' width=120px/>".format(img_url=user.avatar.url, alt='AvatarUser'))
            return mark_safe("<img src='/static/{img_url}' alt='{alt}' width=120px/>".format(img_url=user.avatar.name,
                                                                                             alt='AvatarUser'))


class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['id', 'position', 'career', 'user_username', 'user_mobile', 'user_email', 'user_gender',
                    'salary_expectation']
    search_fields = ['id', 'position', 'career__name', 'user__username', 'user__mobile', 'user__email', ]
    list_filter_horizontal = ['salary_expectation', ]

    # Để cho list_display lấy thông tin
    def career(self, obj):
        return obj.career.name

    # Để cho list_display lấy thông tin
    def user_username(self, obj):
        return obj.user.username

    # Để cho list_display lấy thông tin
    def user_mobile(self, obj):
        return obj.user.mobile

    # Để cho list_display lấy thông tin
    def user_email(self, obj):
        return obj.user.email

    # Để cho list_display lấy thông tin
    def user_gender(self, obj):
        return obj.user.gender



# Tạo inlineModel (Từ model Employer có thể thêm luôn RecruitmentPost)
class RecruitmentPostInline(admin.StackedInline):
    model = RecruitmentPost
    pk_name = 'employer'


class EmployerAdmin(admin.ModelAdmin):
    list_display = ['id', 'position', 'companyName', 'company_type', 'user_username', 'user_mobile', 'user_email',
                    'user_gender', ]
    search_fields = ['id', 'position', 'companyName', 'user__username', 'user__mobile', 'user__email', ]
    # Thêm vào để có thể tạo inlineModel
    inlines = (RecruitmentPostInline,)

    def user_username(self, obj):
        return obj.user.username

    def user_mobile(self, obj):
        return obj.user.mobile

    def user_email(self, obj):
        return obj.user.email

    def user_gender(self, obj):
        return obj.user.gender

    # Để cho list_display lấy thông tin
    def company_type(self, obj):
        return dict(Employer.STATUS_CHOICES)[obj.status]


class AreaAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']


class EmploymentTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'type']
    search_fields = ['id', 'type']


class RecruitmentPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'deadline', 'quantity', 'career_name', 'position', 'companyName', 'employmenttype',
                    'gender', 'location', 'salary']
    search_fields = ['id', 'title', 'career__name', 'position', 'employer__companyName', 'employmenttype__type',
                     'location', 'gender']
    list_filter_horizontal = ['quantity', 'salary']  # Lọc theo chiều ngang => Không hiện thanh kéo

    def career_name(self, obj):
        return obj.career.name

    def companyName(self, obj):
        return obj.employer.companyName


class StatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'role']


class SkillAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class CareerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'applicant_username', 'employer_username', 'interaction__recruitment__title']
    search_fields = ['id', 'applicant__user__username', 'employer__user__username']
    # 'applicant__user__username', 'employer__user__username' : search_fields lấy thông tin thông qua kế thừa model -> khóa ngoại -> Nơi cần lấy thông tin

    # Để cho list_display lấy thông tin: Thông qua kế thừa model -> Khóa ngoại -> Nơi cần lấy thông tin
    def applicant_username(self, obj):
        if obj.applicant:
            return obj.applicant.user.username
        return None

    # Vì lấy chung thông tin tới User nên phải viết thêm 1 hàm def
    # Để cho list_display lấy thông tin: Thông qua kế thừa model -> Khóa ngoại -> Nơi cần lấy thông tin
    def employer_username(self, obj):
        if obj.employer:
            return obj.employer.user.username
        return None

    # Để cho list_display lấy thông tin: Thông qua kế thừa model -> Khóa ngoại -> Nơi lấy thông tin
    def interaction__recruitment__title(self, obj):
        return obj.recruitment.title


class RatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'rating', 'applicant_username', 'employer_username', 'interaction__recruitment__title']
    search_fields = ['id', 'rating', 'applicant__user__username', 'employer__user__username']

    def applicant_username(self, obj):
        if obj.applicant:
            return obj.applicant.user.username
        return None

    def employer_username(self, obj):
        if obj.employer:
            return obj.employer.user.username
        return None

    def interaction__recruitment__title(self, obj):
        return obj.recruitment.title

class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'applicant_username', 'employer_username', 'interaction__recruitment__title']
    search_fields = ['id', 'applicant__user__username', 'employer__user__username']

    def applicant_username(self, obj):
        if obj.applicant:
            return obj.applicant.user.username
        return None

    def employer_username(self, obj):
        if obj.employer:
            return obj.employer.user.username
        return None

    def interaction__recruitment__title(self, obj):
        return obj.recruitment.title



# Tạo trang admin theo cách của mình -> Ghi đè lại cái đã có
class MyAdminSite(admin.AdminSite):
    site_header = 'JOB MANAGEMENT SYSTEM'
    index_title = 'Welcome to the management system'
    site_title = 'Custom by Mtie'
    site_url = "/"

    # Ghi đè lại url đã có
    def get_urls(self):
        return [
            path('stats/', self.stats_view),   # => myadmin/stats, myadmin là cái tạo phía dưới
            path('search/', self.search_by_salary),  # => myadmin/search, myadmin là cái tạo phía dưới
        ] + super().get_urls()

    # Cái này dẫn tới folder templates/
    def stats_view(self, request):
        return TemplateResponse(request, 'admin/jobStats.html', {
            'queryset': dao.count_job_application_quarter_career(),
            'femaleApply': dao.recruitment_posts_with_female_applicants(),
        })

    # Cái này dẫn tới folder templates/
    def search_by_salary(self, request):
        if request.method == 'GET':
            salary = request.GET.get('salary')
            if salary:
                # Lọc các bài đăng có mức lương lớn hơn hoặc bằng mức lương nhập vào
                recruitment_posts = dao.search_salary_recruiment_post(salary)
                return render(request, 'admin/search_salary.html',
                              {'recruitment_posts': recruitment_posts, 'salary': salary,
                               })
        return render(request, 'admin/search_salary.html', {})



# Tạo đối tượng
my_admin_site = MyAdminSite(name='myadmin')  # tạo đường dẫn myadmin thay thế cho admin hiện tại

my_admin_site.register(User, UserAdmin),
my_admin_site.register(Employer, EmployerAdmin),
my_admin_site.register(Applicant, ApplicantAdmin),
my_admin_site.register(Area, AreaAdmin),
my_admin_site.register(EmploymentType, EmploymentTypeAdmin),
my_admin_site.register(RecruitmentPost, RecruitmentPostAdmin),
my_admin_site.register(JobApplication, JobApplicationAdmin),
my_admin_site.register(Status, StatusAdmin),
my_admin_site.register(Skill, SkillAdmin),
my_admin_site.register(Career, CareerAdmin),
my_admin_site.register(Comment, CommentAdmin),
my_admin_site.register(Rating, RatingAdmin),
my_admin_site.register(Permission),
my_admin_site.register(Like, LikeAdmin),
# Register your models here.
admin.site.register(User, UserAdmin),
admin.site.register(Employer, EmployerAdmin),
admin.site.register(Applicant, ApplicantAdmin),
admin.site.register(Area, AreaAdmin),
admin.site.register(EmploymentType, EmploymentTypeAdmin),
admin.site.register(RecruitmentPost, RecruitmentPostAdmin),
admin.site.register(JobApplication, JobApplicationAdmin),
admin.site.register(Status, StatusAdmin),
admin.site.register(Skill, SkillAdmin),
admin.site.register(Career, CareerAdmin),
admin.site.register(Comment, CommentAdmin),
admin.site.register(Rating, RatingAdmin),
admin.site.register(Permission),
admin.site.register(Like, LikeAdmin),
