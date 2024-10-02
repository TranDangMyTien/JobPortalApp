from rest_framework import routers
from jobs import views
from django.urls import path, include


# Tạo đối tượng
router = routers.DefaultRouter()
# Phần đầu tiên là prefix, tiếp đầu ngữ -> Phần đầu mà URL nó tạo ra cho mình
# Phần thứ 2 là viewsest
# "recruitments_post" là đường dẫn URL mà view set sẽ được đăng ký vào.
# views.RecruitmentPostViewSet là view set mà bạn muốn đăng ký.

router.register('recruitments_post', views.RecruitmentPostViewSet, basename="recruitment_post")
router.register('users', views.UserViewSet, basename='users')
router.register('employers', views.EmployerViewSet, basename='employers')
router.register('applicants', views.ApplicantViewSet, basename='applicants')
router.register('careers', views.CareerViewSet, basename='careers')
router.register('employmenttypes', views.EmploymentTypeViewSet, basename='employmenttypes')
router.register('areas', views.AreaViewSet, basename='areas')
router.register('skills', views.SkillViewSet, basename='skills')
# router.register('password-reset', views.PasswordReset, basename='password_reset')
router.register('employer-recruitment-posts', views.EmployerRecruitmentPostViewSet, basename='employer-recruitment-posts')
router.register('find-applicants', views.FindApplicantViewSet, basename='find-applicants')

urlpatterns = [
    path('', include(router.urls)),

    # Phục vụ cho phần đổi mật khẩu
    path('password-reset/', views.PasswordReset.as_view(), name='password-reset'),
    path('password-reset-confirm/', views.ResetPasswordView.as_view(), name='password-reset-confirm'),
    # Phục vụ cho phần kiểm tra sự tồn tại email => Đăng ký User
    path('check-email/', views.EmailCheckAPIView.as_view(), name='check-email'),
    # Kiểm tra sự tồn tại của token
    path('check-token/', views.TokenCheckAPIView.as_view(), name='check-token'),
    # Kiểm tra sự tồn tại của review đã từng review trong bài đăng tuyển dụng
    path('recruitments_post/<int:pk>/review-status/', views.ReviewStatusView.as_view(), name='review_status'),



    # Phần OAuth2
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # Phần đăng nhập với Google
    path(
        "auth/google/callback/login",
        views.GoogleOAuth2LoginCallbackView.as_view(),
        name="google_login_callback",
    ),
    # path(
    #     "facebook/callback/login",
    #     views.FacebookLoginCallbackView.as_view(),
    #     name="facebook_login_callback",
    # ),

    # Phần Chat
    path('chat/create-or-get/', views.create_or_get_chat, name='create_or_get_chat'),
    path('chat/<int:chat_id>/messages/', views.get_chat_messages, name='get_chat_messages'),
    path('chat/<int:chat_id>/send/', views.send_message, name='send_message'),
    # Danh sách phòng chat của employer
    path('chats/', views.get_employer_chats, name='get_employer_chats'),
    path('applicant/chats/', views.get_applicant_chats, name='get_applicant_chats'),
    path('create_post/', views.RecruitmentPostCreateView.as_view(), name='recruitment-post-create'),
    path('applications/', views.ApplicantJobApplicationsListView.as_view(), name='applicant-job-applications'),
    path('job-suggestions/', views.RecommendedJobsView.as_view(), name='job-suggestions'),
    path('list_applications_for_post/<int:post_id>/', views.ListApplicationsForPost.as_view(), name='list_applications_for_post'),
    # path('applications/status/<int:application_id>/', views.update_application_status, name='update_application_status'),
    path('jobapplication/<int:pk>/status/', views.JobApplicationStatusUpdateView.as_view(), name='jobapplication-status-update'),
]