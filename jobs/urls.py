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
urlpatterns = [
    path('', include(router.urls)),

    # Phần OAuth2
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

]