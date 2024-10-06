from django.contrib import admin
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from jobs.models import (User, Employer, Applicant, Area, EmploymentType, RecruitmentPost, JobApplication, Status,
                         Skill, Notification, UserNotification,
                         Career, Review, PasswordResetToken, Message, Chat)
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
import cloudinary
from django.urls import path
from jobs import dao
from django.shortcuts import render
from django.contrib.auth.models import Permission  # Phần chứng thực
from oauth2_provider.models import AccessToken, Application, Grant, RefreshToken, IDToken
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.core.mail import send_mail

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
    # def clean(self):
    #     cleaned_data = super().clean()
    #     is_superuser = cleaned_data.get('is_superuser')
    #     is_staff = cleaned_data.get('is_staff')
    #     is_employer = cleaned_data.get('is_employer')
    #     is_applicant = cleaned_data.get('is_applicant')

    #     # If the user is not a superuser or staff, ensure they select one of the roles
    #     if not is_superuser and not is_staff:
    #         if is_employer and is_applicant:
    #             raise forms.ValidationError("Can only be selected as employer or applicant.")
    #         if not is_employer and not is_applicant:
    #             raise forms.ValidationError("Must choose whether to be the employer or the applicant.")

    #     return cleaned_data

    class Meta:
        model = User
        fields = ('username', 'email', 'mobile', 'gender', 'is_employer', 'is_staff', 'is_superuser', 'avatar', 'first_name', 'last_name')

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(render_value=True), required=False)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput(render_value=True), required=False)


    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get("password1")

        if password1:  # Only set a new password if one is provided
            user.set_password(password1)

        if commit:
            user.save()
        return user


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'mobile', 'email', 'gender', 'is_superuser', 'is_staff', 'is_employer']
    search_fields = ['id', 'mobile', 'username', 'mobile', 'email', 'gender']
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


class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        skills = cleaned_data.get('skills')
        areas = cleaned_data.get('areas')

        if skills and skills.count() > 5:
            raise forms.ValidationError("You can select a maximum of 5 skills.")

        if areas and areas.count() > 3:
            raise forms.ValidationError("You can select a maximum of 3 areas.")

        return cleaned_data

# Tạo inlineModel (Từ model Applicant có thể thêm luôn JobApplication)
class JobApplicationInline(admin.StackedInline):
    model = JobApplication
    pk_name = 'applicant'


class ApplicantAdmin(admin.ModelAdmin):
    form = ApplicantForm
    list_display = ['id', 'position', 'career', 'user_username', 'user_mobile', 'user_email', 'get_user_gender_display', 'salary_expectation']
    search_fields = ['id', 'position', 'career__name', 'user__username', 'user__mobile', 'user__email', ]
    list_filter_horizontal = ['salary_expectation', ]
    # inlines = (JobApplicationInline,)

    def career(self, obj):
        return obj.career.name if obj.career else '-'

    def user_username(self, obj):
        return obj.user.username

    def user_mobile(self, obj):
        return obj.user.mobile

    def user_email(self, obj):
        return obj.user.email

    def get_user_gender_display(self, obj):
        return obj.user.get_gender_display()

    career.admin_order_field = 'career__name'
    user_username.admin_order_field = 'user__username'
    user_mobile.admin_order_field = 'user__mobile'
    user_email.admin_order_field = 'user__email'
    get_user_gender_display.short_description = 'Gender' # Chuyển đổi tên cho ngắn gọn




# Tạo inlineModel (Từ model Employer có thể thêm luôn RecruitmentPost)
class RecruitmentPostInline(admin.StackedInline):
    model = RecruitmentPost
    pk_name = 'employer'


class EmployerAdmin(admin.ModelAdmin):
    list_display = ['id', 'position', 'companyName', 'company_type', 'user_username', 'user_mobile', 'user_email', 'get_user_gender_display']
    search_fields = ['id', 'position', 'companyName', 'user__username', 'user__mobile', 'user__email']
    # inlines = (RecruitmentPostInline,)

    def user_username(self, obj):
        return obj.user.username

    def user_mobile(self, obj):
        return obj.user.mobile

    def user_email(self, obj):
        return obj.user.email

    def get_user_gender_display(self, obj):
        return obj.user.get_gender_display()

    def company_type(self, obj):
        return dict(Employer.STATUS_CHOICES)[obj.status]

    user_username.admin_order_field = 'user__username'
    user_mobile.admin_order_field = 'user__mobile'
    user_email.admin_order_field = 'user__email'
    get_user_gender_display.short_description = 'Gender'


class AreaAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']


class EmploymentTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'type']
    search_fields = ['id', 'type']


class RecruitmentPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'deadline', 'quantity', 'career_name', 'position', 'companyName', 'employmenttype',
                    'gender', 'location', 'salary', 'reported']
    search_fields = ['id', 'title', 'career__name', 'position', 'employer__companyName', 'employmenttype__type',
                     'location', 'gender']
    list_filter_horizontal = ['quantity', 'salary']  # Lọc theo chiều ngang => Không hiện thanh kéo

    def career_name(self, obj):
        return obj.career.name

    def companyName(self, obj):
        return obj.employer.companyName

    # Custom function để hiển thị trạng thái reported
    def reported(self, obj):
        if obj.reported:
            return format_html(
                '<span style="color:red;">Yes</span>')  # Nếu bài đăng bị báo cáo, hiển thị "Yes" với màu đỏ
        else:
            return format_html(
                '<span style="color:green;">No</span>')  # Nếu bài đăng không bị báo cáo, hiển thị "No" với màu xanh lá cây

    reported.short_description = 'Reported'  # Đặt tên cho cột "Reported" trong trang quản trị
    reported.admin_order_field = 'reported'  # Cho phép sắp xếp bài đăng theo trạng thái reported

    # Phần tìm kiếm lương lớn hơn hoặc bằng
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Nếu có mức lương được nhập vào trong thanh tìm kiếm
        if search_term.isdigit():
            salary = int(search_term)
            queryset |= self.model.objects.filter(salary__gte=salary)

        return queryset, use_distinct


class StatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'role']


class SkillAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class CareerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

# class CommentInline(admin.StackedInline):
#     model = Comment  # Chỉ định rằng InlineAdmin này sẽ hiển thị các comment con của một comment cha.
#     fk_name = 'parent'  # Chỉ định khóa ngoại liên kết các comment con với comment cha là parent.
#     extra = 0  # Không hiển thị trường để thêm comment con mới khi chưa có comment cha.
#     # Chỉ định các trường sẽ hiển thị trong InlineAdmin.
#     fields = ['content', 'user', 'recruitment']
#     # Đánh dấu các trường applicant, employer, recruitment chỉ để đọc, không cho phép chỉnh sửa trong InlineAdmin.
#     readonly_fields = ['recruitment']


# class CommentAdmin(admin.ModelAdmin):
#     list_display = ['id', 'content','interaction__user__username', 'interaction__recruitment__title','parent__interaction__user__username','parent__interaction__recruitment__title']
#     search_fields = ['id', 'user__username']
#     # 'user__username' : search_fields lấy thông tin thông qua kế thừa model -> khóa ngoại -> Nơi cần lấy thông tin
#     inlines = [CommentInline]
#
#     # Để cho list_display lấy thông tin: Thông qua kế thừa model -> Khóa ngoại -> Nơi cần lấy thông tin
#     def interaction__user__username(self, obj):
#         if obj.user:
#             return obj.user.username
#         return None
#
#     # # Vì lấy chung thông tin tới User nên phải viết thêm 1 hàm def
#     # # Để cho list_display lấy thông tin: Thông qua kế thừa model -> Khóa ngoại -> Nơi cần lấy thông tin
#     # def employer_username(self, obj):
#     #     if obj.employer:
#     #         return obj.employer.user.username
#     #     return None
#
#     def parent__interaction__user__username(self, obj):
#         if obj.parent:
#             return obj.parent.user.username
#         return None
#
#     def parent__interaction__recruitment__title(self, obj):
#         if obj.parent:
#             return obj.parent.recruitment.title
#         return None
#
#     # Để cho list_display lấy thông tin: Thông qua kế thừa model -> Khóa ngoại -> Nơi lấy thông tin
#     def interaction__recruitment__title(self, obj):
#         if obj.recruitment:
#             return obj.recruitment.title
#         return None



# class RatingAdmin(admin.ModelAdmin):
#     list_display = ['id', 'rating', 'user_username', 'interaction__recruitment__title']
#     search_fields = ['id', 'rating', 'user__username', 'user__username']
#
#     def user_username(self, obj):
#         if obj.user:
#             return obj.user.username
#         return None
#
#     def interaction__recruitment__title(self, obj):
#         return obj.recruitment.title


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'rating', 'content', 'user_username', 'interaction__recruitment__title']
    search_fields = ['id', 'rating', 'user__username']
    def user_username(self, obj):
        if obj.user:
            return obj.user.username
        return None
    def interaction__recruitment__title(self, obj):
        return obj.recruitment.title

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'created_date']
    search_fields = ['content']

class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('user__username', 'notification__content')

# Hàm kiểm tra tùy chỉnh để xác định người dùng có phải là admin không
def is_admin(user):
    return user.is_superuser or user.is_staff

# Tạo trang admin theo cách của mình -> Ghi đè lại cái đã có
class MyAdminSite(admin.AdminSite):
    site_header = 'OU JOB MANAGEMENT SYSTEM'
    index_title = 'Welcome to the management system'
    site_title = 'Custom by Mtie'
    site_url = "/"



    # Ghi đè lại url đã có
    def get_urls(self):
        return [
            path('stats/', self.stats_view),   # => myadmin/stats, myadmin là cái tạo phía dưới
            path('search/', self.search_by_salary),  # => myadmin/search, myadmin là cái tạo phía dưới
            path('mail/', self.mail_view)
        ] + super().get_urls()
    # Bộ trang trí phương thức để giới hạn quyền truy cập vào stats_view
    @method_decorator(user_passes_test(is_admin))
    # Cái này dẫn tới folder templates/
    def stats_view(self, request):
        return TemplateResponse(request, 'admin/jobStats.html', {
            'queryset': dao.count_job_application_quarter_career(),
            'femaleApply': dao.recruitment_posts_with_female_applicants(),
        })
    @method_decorator(user_passes_test(is_admin))
    def mail_view(self, request):
        if request.method == 'POST':
            name = request.POST.get('full-name')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            recipient_email = request.POST.get('recipient-email')  # Lấy địa chỉ email người nhận từ form

            data = {
                'name': name,
                'subject': subject,
                'message': message
            }

            message_content = '''
            New message: {}
            From: {}
            '''.format(data['message'], data['name'])

            send_mail(data['subject'], message_content, '',
                      [recipient_email])  # Gửi email đến địa chỉ người nhận từ form

        return render(request, 'admin/mail.html', {})

    # Cái này dẫn tới folder templates/
    @method_decorator(user_passes_test(is_admin))
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


class GrantAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', 'application', 'expires', 'redirect_uri')


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'token', 'application', 'expires', 'scope')


class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'token', 'application', 'access_token')


class IDTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'user')


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_id', 'user', 'authorization_grant_type', 'client_type')

# class ChatAdmin(admin.ModelAdmin):
#     list_display = ('id', 'applicant', 'employer', 'created_at')
# class MessageAdmin(admin.ModelAdmin):
#     list_display = ('id', 'chat', 'sender', 'text', 'created_at')




class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'user_email')
    actions = ['delete_expired_tokens']

    def user_email(self, obj):
        """
        Hiển thị email của người dùng liên kết với token.
        """
        return obj.user.email

    user_email.short_description = 'User Email'  # Tiêu đề cột trong bảng quản lý

    def delete_expired_tokens(self, request, queryset):
        now = timezone.now()
        expired_tokens = queryset.filter(created_at__lt=now - timezone.timedelta(minutes=5))
        count, _ = expired_tokens.delete()
        self.message_user(request, f'Successfully deleted {count} expired tokens.')

    delete_expired_tokens.short_description = 'Delete expired tokens'

class MessageInline(admin.TabularInline):  # Sử dụng TabularInline cho các tin nhắn
    model = Message
    extra = 1  # Số lượng form trống hiển thị

class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'applicant', 'employer', 'created_at']
    search_fields = ['applicant__user__username', 'employer__user__username']
    inlines = [MessageInline]  # Bao gồm các tin nhắn inline

class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'get_sender_username', 'text', 'created_at']
    search_fields = ['sender__username', 'text']

    def get_sender_username(self, obj):
        return obj.sender.username  # Trả về tên người gửi

    get_sender_username.short_description = 'Sender'  # Đặt tiêu đề cho cột

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
# my_admin_site.register(Comment, CommentAdmin),
# my_admin_site.register(Rating, RatingAdmin),
my_admin_site.register(Review, ReviewAdmin),
my_admin_site.register(Permission),
my_admin_site.register(Notification, NotificationAdmin)
my_admin_site.register(AccessToken, AccessTokenAdmin),
my_admin_site.register(Application, ApplicationAdmin),
my_admin_site.register(IDToken, IDTokenAdmin),
my_admin_site.register(Grant, GrantAdmin)
my_admin_site.register(RefreshToken, RefreshTokenAdmin)
my_admin_site.register(UserNotification, UserNotificationAdmin)
my_admin_site.register(PasswordResetToken, PasswordResetTokenAdmin)
my_admin_site.register(Chat, ChatAdmin)
my_admin_site.register(Message, MessageAdmin)






# # Register your models here.
# admin.site.register(User, UserAdmin),
# admin.site.register(Employer, EmployerAdmin),
# admin.site.register(Applicant, ApplicantAdmin),
# admin.site.register(Area, AreaAdmin),
# admin.site.register(EmploymentType, EmploymentTypeAdmin),
# admin.site.register(RecruitmentPost, RecruitmentPostAdmin),
# admin.site.register(JobApplication, JobApplicationAdmin),
# admin.site.register(Status, StatusAdmin),
# admin.site.register(Skill, SkillAdmin),
# admin.site.register(Career, CareerAdmin),
# admin.site.register(Comment, CommentAdmin),
# admin.site.register(Rating, RatingAdmin),
# admin.site.register(Permission),
# admin.site.register(Like, LikeAdmin),
