import os

import filters
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from social_core.backends import stripe

from jobs.models import RecruitmentPost, Review, UserProfile, Chat, Invoice
from jobs import serializers
from jobs import paginators
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import viewsets, generics, permissions, status, parsers
from rest_framework.decorators import action, api_view, permission_classes
from jobs import dao
from .models import JobApplication, Employer, Applicant, User, Notification, Status, Like, Message
from .paginators import ReviewPaginator, ApplicantPagination, RecruitmentPostPaginator
from .serializers import (JobApplicationSerializer, AuthenticatedRecruitmentPostSerializer,
                          Career, EmploymentType, Area,
                          RecruitmentPostSerializer, NotificationSerializer, Skill,
                          CreateJobApplicationStatusSerializer, PasswordResetSerializer, EmailCheckSerializer,
                          TokenCheckSerializer, CreateReviewSerializer, ReviewSerializer, ReviewStatusSerializer,
                          CreatePostSerializer, ApplicantSerializer, ViewApplicantSerializer,
                          JobApplicationStatusSerializer, RegistereEmployerSerializer
                          )
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .filters import RecruitmentPostFilter
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date
from jobs import perms
from rest_framework import viewsets, filters

# Create your views here.
# Làm việc với GenericViewSet (generics.ListAPIView)
# Một ViewSet có thể add nhiều api
# ListAPIView = GET : Xem danh sách
# RetrieveAPIView = GET : Xem chi tiết
# DestroyAPIView = DELETE : Xóa
# CreateAPIView = POST : Tạo mới
# UpdateAPIView = PUT/PATCH = Cập nhật toàn bộ/ một phần
# ListCreateAPIView = GET + POST : Xem danh sách + tạo mới
# RetrieveUpdateAPIView = GET + PUT + PATCH : Xem chi tiết + cập nhật toàn phần + cập nhật một phần
# RetrieveDestroyAPIView = GET + DELETE : Xem chi tiết + xóa
# RetrieveUpdateDestroyAPIView = GET + PUT + PATCH + DELETE : Xem chi tiết + cập nhật toàn phần + cập nhật một phần + xóa

class RecruitmentPostCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CreatePostSerializer
    def post(self, request):
        serializer = serializers.CreatePostSerializer(data=request.data)
        if serializer.is_valid():
            recruitment_post = serializer.save()
            return Response(CreatePostSerializer(recruitment_post).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecruitmentPostViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.ListAPIView, generics.CreateAPIView):
    # Trong Django, queryset là một biến được sử dụng trong các API view để xác định tập hợp các đối tượng dữ liệu từ cơ sở dữ liệu
    # mà API view sẽ hoạt động trên đó.
    # queryset = RecruitmentPost.objects.all().order_by('id')
    queryset = RecruitmentPost.objects.filter(active=True).order_by('id')
    # Trong Django REST Framework, khi bạn thiết lập một API view, bạn cần xác định loại dữ liệu nào sẽ được sử dụng để biểu diễn dữ liệu trả về từ API đó.
    # Điều này được thực hiện thông qua việc chỉ định một lớp serializer bằng cách sử dụng thuộc tính serializer_class.
    # Đoạn mã này đang chỉ định rằng API view sẽ sử dụng lớp serializer RecruitmentPostSerializer từ module serializers
    # Nói cách khác, khi bạn truy vấn dữ liệu từ model RecruitmentPost, dữ liệu sẽ được trả về dưới dạng các đối tượng RecruitmentPost, và sau đó được chuyển đổi thành định dạng JSON
    # (hoặc XML) thông qua serializer này trước khi được trả về từ API.
    serializer_class = serializers.RecruitmentPostSerializer  # Tùy chỉnh cách dữ liệu được biểu diễn và xử lý trước khi nó được gửi đến client

    # Thiết lập lớp phân trang (pagination class) cho một API view cụ thể.
    pagination_class = paginators.RecruitmentPostPaginator

    # Phần filter
    # GET /recruitments_post/?min_salary=1000000:
    # Lấy danh sách tất cả các bài đăng có mức lương yêu cầu từ 1,000,000 VND trở lên
    # GET /recruitments_post/?max_salary=2000000:
    # Lấy danh sách tất cả các bài đăng có mức lương yêu cầu dưới 2,000,000 VND.
    # GET /recruitments_post/?min_salary=1000000&max_salary=2000000:
    # Lấy danh sách các bài đăng có mức lương yêu cầu từ 1,000,000 VND đến 2,000,000 VND.
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecruitmentPostFilter

    def get_serializer_class(self):
        if self.action == 'apply':
            return serializers.CreateJobApplicationStatusSerializer
        if self.action == 'like':
            return serializers.AuthenticatedRecruitmentPostSerializer
        if self.action == 'hide_post':
            return serializers.HideRecruitmentPostSerializer
        if self.action in ['create', 'partial_update']:
            return serializers.CreateRecruitmentPostSerializer
        if self.action in ['create_reviews']:
            return serializers.CreateReviewSerializer
        if self.action in ['get_reviews', 'update_reviews', 'delete_review']:
            return serializers.ReviewSerializer
        if self.action in ['list_apply', 'view_application']:
            return serializers.JobApplicationSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ['create_comment', 'reply_comment', 'report', 'create_reviews', 'like', 'apply', 'create' ]:
            return [permissions.IsAuthenticated()]
        # if self.action in ['create']:
        #     return [perms.EmIsAuthenticated()]
        if self.action in ['edit_post', 'delete_recruitment_post', 'hide_post']:
            return [perms.EmOwnerAuthenticated()]
        if self.action in [
            'num_applications', 'count_likes', 'partial_update_application',
            'delete_application', 'partial_update_rating', 'delete_rating',
            'delete_comment', 'delete_reply', 'partial_update_comment',
            'partial_update_reply', 'delete_review',  'update_reviews'
        ]:
            return [perms.IsAdminOrSelf()]
        if self.action in ['list_apply', 'view_application']:
            return [perms.IsAdminOrSelfOrEmIsAuthenticated()]
        if self.action in ['most_liked_post', 'list_report']:
            return [perms.AdminIsAuthenticated()]

        return [permissions.AllowAny()]

    # Không endpoint
    # Tìm kiếm các bài đăng theo tiêu đề: /recruitments_post/?title=example_title
    # Tìm kiếm các bài đăng theo id của nhà tuyển dụng: /recruitments_post/?employer_id=example_employer_i
    # Tìm kiếm các bài đăng theo ngành nghề: /recruitments_post/?career=example_career
    # Tìm kiếm các bài đăng theo loại hình công việc: /recruitments_post/?employment_type=example_employment_type
    # Tìm kiếm các bài đăng theo địa điểm: /recruitments_post/?location=example_location
    # Tìm kiếm kết hợp các tiêu chí: /recruitments_post/?title=example_title&employer_id=example_employer_id&career=example_career
    # Tìm kiếm các bài đăng theo id của loại hình công việc : https://tdmtien.pythonanywhere.com/recruitments_post/?type_id=2
    def get_queryset(self):
        # Code xử lý lọc dữ liệu ở đây
        queries = self.queryset

        # Lọc các bài đăng tuyển dụng đã hết thời hạn
        for q in queries:
            if q.deadline <= timezone.now().date():
                q.active = False
                q.save()
            queries = queries.filter(active=True)

        # Kiểm tra nếu hành động là 'list' (tức là yêu cầu danh sách các bài đăng)
        if self.action == 'list':
            title = self.request.query_params.get('title')
            employer_id = self.request.query_params.get('employer_id')
            career = self.request.query_params.get('career')
            employment_type = self.request.query_params.get('employment_type')
            location = self.request.query_params.get('location')
            type_id = self.request.query_params.get('type_id')

            # Lọc theo tiêu đề
            if title:
                queries = queries.filter(title__icontains=title)

            # Lọc theo id của nhà tuyển dụng
            if employer_id:
                queries = queries.filter(employer_id=employer_id)

            # Lọc theo ngành nghề
            if career:
                queries = queries.filter(career__name__icontains=career)

            # Lọc theo loại hình công việc
            if employment_type:
                queries = queries.filter(employmenttype__type__icontains=employment_type)

            # Lọc theo địa điểm
            if location:
                queries = queries.filter(location__icontains=location)

            # Lọc theo id của loại hình công việc => Phục vụ cho phần render bên FE
            if type_id:
                queries = queries.filter(employmenttype_id=type_id)

        return queries

    # API lọc bài tuyển dụng theo mức lương
    # /recruitments_post/filter_salary/?min_salary=5000000 => bài đăng có mức lương từ 5,000,000 VND trở lên
    # /recruitments_post/filter_salary/?max_salary=10000000 => bài đăng có mức lương dưới 10,000,000 VND
    # /recruitments_post/filter_salary/?min_salary=5000000&max_salary=10000000 => bài đăng có mức lương từ 5000000 đến 10000000
    @action(detail=False, methods=['get'])
    def filter_salary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        min_salary = request.query_params.get('min_salary')
        max_salary = request.query_params.get('max_salary')

        if min_salary is not None:
            queryset = queryset.filter(salary__gte=min_salary)
        if max_salary is not None:
            queryset = queryset.filter(salary__lte=max_salary)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # API chỉnh sửa bài đăng tuyển dụng
    # /recruitment-posts/{pk}/edit-post/
    @action(methods=['patch'], detail=True, url_path='edit-post', url_name='edit_post')
    def edit_post(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Kiểm tra quyền chỉnh sửa
            if request.user != recruitment_post.employer.user:
                return Response({"error": "You do not have permission to edit this post."},
                                status=status.HTTP_403_FORBIDDEN)

            # Sử dụng serializer để cập nhật một phần thông tin bài đăng
            serializer = RecruitmentPostSerializer(recruitment_post, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xóa bài đăng tuyển dụng
    # /recruitments_post/pk/delete/
    @action(methods=['delete'], detail=True, url_path='delete', url_name='delete')
    def delete_recruitment_post(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Kiểm tra quyền xóa bài đăng tuyển dụng
            # Ví dụ: chỉ người dùng là admin hoặc người tạo bài đăng mới có quyền xóa
            if request.user != recruitment_post.employer.user:
                return Response({"error": "You do not have permission to delete this recruitment post."},
                                status=status.HTTP_403_FORBIDDEN)

            # Xóa bài đăng tuyển dụng
            recruitment_post.delete()
            return Response({"message": "Recruitment post deleted successfully."},
                            status=status.HTTP_204_NO_CONTENT)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xem danh sách bài đăng tuyển dụng phổ biến (được apply nhiều) (giảm dần theo số lượng apply)
    # /recruitments_post/popular/
    @action(detail=False, methods=['get'])
    def popular(self, request):
        try:
            # Lấy danh sách các bài đăng tuyển dụng được sắp xếp theo số lượng apply giảm dần
            # Truy vấn ngược
            recruitment_posts = dao.recruiment_posts_by_appy()
            page = self.paginate_queryset(recruitment_posts)
            # Phân trang cho danh sách bài đăng
            # paginator = paginators.RecruitmentPostPaginator()
            # paginated_recruitment_posts = paginator.paginate_queryset(recruitment_posts, request)
            if page is not None:
                serializer = RecruitmentPostSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = serializers.RecruitmentPostSerializer(recruitment_posts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment posts not found."}, status=status.HTTP_404_NOT_FOUND)

    # API Đếm số lượng apply của 1 bài đăng theo id
    # /recruitments_post/<pk>/num_applications
    @action(detail=True, methods=['get'])
    def num_applications(self, request, pk=None):
        try:
            num_applications = dao.count_apply_by_id_recruiment_post(pk)
            # Trả về số lượng đơn ứng tuyển dưới dạng JSON
            return Response({"num_applications": num_applications}, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API lấy danh sách các apply của 1 bài đăng (theo id)
    # /recruitments_post/<pk>/list_apply/
    @action(detail=True, methods=['get'])
    def list_apply(self, request, pk=None):
        try:
            # Lấy danh sách các ứng tuyển từ DAO
            applications = dao.recruiment_posts_apply_by_ID(pk)

            # Kiểm tra nếu bài đăng tuyển dụng không tồn tại
            if not applications:
                return Response({"detail": "No RecruitmentPost matches the given query."},
                                status=status.HTTP_404_NOT_FOUND)

            # Phân trang danh sách các ứng tuyển
            paginator = paginators.ApplicationPagination()
            paginated_applications = paginator.paginate_queryset(applications, request, view=self)

            # Serialize danh sách các ứng tuyển đã phân trang
            serializer = JobApplicationSerializer(paginated_applications, many=True)

            # Trả về danh sách các ứng tuyển đã phân trang
            return paginator.get_paginated_response(serializer.data)

        except RecruitmentPost.DoesNotExist:
            # Trả về thông báo lỗi nếu không tìm thấy bài đăng tuyển dụng
            return Response({"detail": "No RecruitmentPost matches the given query."}, status=status.HTTP_404_NOT_FOUND)

    # API xem chi tiết một đơn ứng tuyển của một bài đăng tuyển dụng
    # /recruitments_post/<pk>/applications/<application_id>/
    @action(detail=True, methods=['get'], url_path='applications/(?P<application_id>\d+)', url_name='view_application')
    def view_application(self, request, pk=None, application_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy đơn ứng tuyển từ application_id
            application = get_object_or_404(JobApplication, pk=application_id)

            # Kiểm tra xem đơn ứng tuyển có thuộc về bài đăng tuyển dụng không
            if application.recruitment != recruitment_post:
                return Response({"error": "Job application does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Serialize đơn ứng tuyển và trả về chi tiết
            serializer = JobApplicationSerializer(application)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job application not found."}, status=status.HTTP_404_NOT_FOUND)

    # API like bài đăng tuyển dụng
    # /recruitments_post/{id}/like/
    @action(methods=['post'], detail=True, url_path='like')
    def like(self, request, pk=None):
        recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)
        user = request.user

        # Xác định hoặc tạo mới đối tượng Like
        like_instance, created = Like.objects.get_or_create(recruitment=recruitment_post, user=user)

        # Nếu đã tồn tại, chuyển đổi trạng thái active (like/unlike)
        if not created:
            like_instance.active = not like_instance.active
            like_instance.save()

        # Serialize lại recruitment_post sau khi thực hiện hành động like/unlike
        serializer = AuthenticatedRecruitmentPostSerializer(recruitment_post)

        return Response(serializer.data, status=status.HTTP_200_OK)

    # Viết API đếm xem mỗi bài đăng có bao nhiêu lượt like, dựa trên ID bài đăng (do người dùng nhập)
    # /recruitments_post/<pk>/count_likes/
    @action(detail=True, methods=['get'])
    def count_likes(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk (primary key)
            recruitment_post = RecruitmentPost.objects.get(pk=pk)
            # Đếm số lượt like của bài đăng
            num_likes = recruitment_post.like_set.count()
            # Trả về kết quả
            return Response({"count_likes": num_likes}, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # Viết API xem bài đăng tuyển được yêu thích nhất (dùng first)
    # /recruitments_post/most_liked_post/
    @action(detail=False, methods=['get'])
    def most_liked_post(self, request):
        try:
            most_liked_post = dao.recruiment_posts_most_like_first_by_ID()
            # Serialize bài đăng được yêu thích nhất
            serializer = serializers.RecruitmentPostSerializer(most_liked_post)
            # Trả về kết quả
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "No recruitment post found."}, status=status.HTTP_404_NOT_FOUND)

    # Viết API ẩn bài đăng tuyển dựa theo ID (người dùng nhập)
    # /recruitments_post/<pk>/hide_post/
    @action(detail=True, methods=['post'])
    def hide_post(self, request, pk=None):
        try:
            post = RecruitmentPost.objects.get(pk=pk)
            if request.method == 'POST':
                post.active = False
                post.save()
                return Response(data=serializers.HideRecruitmentPostSerializer(post).data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # Viết API xem bài đăng tuyển mới nhất
    # /recruitments_post/newest/
    @action(detail=False, methods=['get'])
    def newest(self, request):
        try:
            # Lấy danh sách các bài đăng tuyển mới nhất bằng cách sắp xếp theo trường created_date giảm dần
            newest_posts = RecruitmentPost.objects.order_by('-created_date').all()
            page = self.paginate_queryset(newest_posts)  # Phân trang queryset

            if page is not None:
                serializer = RecruitmentPostSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = RecruitmentPostSerializer(newest_posts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "No recruitment posts found."}, status=status.HTTP_404_NOT_FOUND)

    # API báo cáo bài đăng tuyển dụng
    # /recruitments_post/<pk>/report/
    @action(detail=True, methods=['patch'])
    def report(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk (primary key)
            recruitment_post = RecruitmentPost.objects.get(pk=pk)
            # Đánh dấu bài đăng tuyển dụng đã được báo cáo
            recruitment_post.reported = True
            recruitment_post.save()
            return Response({"message": "Recruitment post reported successfully."}, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xem danh sách các bài đăng tuyển dụng bị report
    # Endpoint: /recruitments_post/list_report/
    @action(detail=False, methods=['get'])
    def list_report(self, request):
        try:
            # Lấy danh sách các bài đăng tuyển dụng bị report
            reported_posts = RecruitmentPost.objects.filter(reported=True)
            page = self.paginate_queryset(reported_posts)  # Phân trang queryset

            if page is not None:
                serializer = RecruitmentPostSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            # Serialize danh sách các bài đăng tuyển dụng
            serializer = RecruitmentPostSerializer(reported_posts, many=True)
            # Trả về danh sách các bài đăng tuyển dụng dưới dạng JSON
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "No reported recruitment posts found."}, status=status.HTTP_404_NOT_FOUND)

    # API ứng tuyển vào một bài đăng tuyển dụng
    # /recruitments_post/<pk_post>/applicant/<pk_applicant>/apply/
    @action(methods=['post'], detail=False, url_path='(?P<pk_post>\d+)/applicant/(?P<pk_applicant>\d+)/apply')
    def apply(self, request, pk_post=None, pk_applicant=None):
        try:
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk_post)
            applicant = get_object_or_404(Applicant, pk=pk_applicant)

            # Lấy đối tượng Status tương ứng với giá trị 'Pending'
            status_pending = get_object_or_404(Status, role='Pending')

            # Tạo một đối tượng JobApplication mới từ recruitment_post và thiết lập applicant
            job_application = JobApplication.objects.create(
                recruitment=recruitment_post,
                applicant=applicant,
                is_student=request.data.get('is_student', False),
                coverLetter=request.data.get('coverLetter'),
                status=status_pending  # Gán đối tượng status
            )

            # Sử dụng serializer để trả về dữ liệu của đối tượng JobApplication mới tạo
            serializer = CreateJobApplicationStatusSerializer(job_application)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

        except Applicant.DoesNotExist:
            return Response({"error": "Applicant not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # API cập nhật một phần đơn ứng tuyển vào bài đăng tuyển dụng
    # /recruitments_post/{pk}/applications/{application_id}/partial-update/
    @action(detail=True, methods=['patch'], url_path='applications/(?P<application_id>\d+)/partial-update',
            url_name='partial_update_application')
    def partial_update_application(self, request, pk=None, application_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy đơn ứng tuyển từ application_id
            application = get_object_or_404(JobApplication, pk=application_id)

            # Kiểm tra xem đơn ứng tuyển có thuộc về bài đăng tuyển dụng không
            if application.recruitment != recruitment_post:
                return Response({"error": "Job application does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền chỉnh sửa đơn ứng tuyển: Người viết ứng tuyển và admin mới được cập nhật
            if not request.user.is_staff and request.user != application.applicant.user:
                return Response({"error": "You do not have permission to update this job application."},
                                status=status.HTTP_403_FORBIDDEN)

            # Cập nhật một phần của đơn ứng tuyển
            for k, v in request.data.items():
                setattr(application, k, v)  # Thay vì viết application.key  = value
            application.save()

            return Response(serializers.JobApplicationSerializer(application).data, status=status.HTTP_200_OK)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job application not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xóa đơn ứng tuyển vào bài đăng tuyển dụng
    # /recruitments_post/{pk}/applications/{application_id}/delete/
    @action(detail=True, methods=['delete'], url_path='applications/(?P<application_id>\d+)/delete',
            url_name='delete_application')
    def delete_application(self, request, pk=None, application_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy đơn ứng tuyển từ application_id
            application = get_object_or_404(JobApplication, pk=application_id)

            # Kiểm tra xem đơn ứng tuyển có thuộc về bài đăng tuyển dụng không
            if application.recruitment != recruitment_post:
                return Response({"error": "Job application does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền xóa đơn ứng tuyển
            if request.user != application.applicant.user and not request.user.is_staff:
                return Response({"error": "You do not have permission to delete this job application."},
                                status=status.HTTP_403_FORBIDDEN)

            # Xóa đơn ứng tuyển
            application.delete()
            return Response({"message": "Job application deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job application not found."}, status=status.HTTP_404_NOT_FOUND)

    # API tạo đánh giá một bài tuyển dụng
    # /recruitments_post/<pk>/reviews/
    @action(methods=['post'], detail=True, url_path='review', url_name='review')
    def create_reviews(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Kiểm tra xem người dùng đã đánh giá bài đăng này chưa
            existing_rating = Review.objects.filter(recruitment=recruitment_post, user=request.user).first()
            if existing_rating:
                return Response({"error": "You have already reviewed this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            reviews_data = {
                'recruitment': recruitment_post.id,
                'rating': request.data.get('rating', 5),  # Mặc định là 5 nếu không cung cấp
                'user': request.user.id,
                'content': request.data.get('content')
            }

            serializer = CreateReviewSerializer(data=reviews_data, context={'user': request.user})
            serializer.is_valid(raise_exception=True)
            # Lưu serializer với recruitment được tự động điền từ recruitment_post
            serializer.save()

            # Trả về thông tin về đánh giá mới được tạo
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # Tạo API xem danh sách reviews
    # /recruitments_post/<pk>/reviews/
    @action(methods=['get'], detail=True, url_path='reviews', url_name='reviews')
    def get_reviews(self, request, pk=None):
        # Lấy bài đăng tuyển dụng từ pk
        recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

        # Lấy tất cả các review liên quan đến bài đăng tuyển dụng này
        reviews = recruitment_post.review_set.all()

        # Áp dụng phân trang
        paginator = ReviewPaginator()
        page = paginator.paginate_queryset(reviews, request)

        # Nếu có phân trang, sử dụng paginator để tạo response
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Trường hợp không có phân trang (ít dữ liệu), trả về toàn bộ
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # API cập nhật Review (một phần)
    # /recruitments_post/pk/update-reviews/review_id/
    @action(methods=['patch'], detail=True, url_path='update-reviews/(?P<review_id>[^/.]+)', url_name='update_reviews')
    def update_reviews(self, request, pk=None, review_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy review cần cập nhật
            review = get_object_or_404(Review, pk=review_id)

            # Kiểm tra xem review có thuộc về bài đăng tuyển dụng không
            if review.recruitment != recruitment_post:
                return Response({"error": "Review does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền chỉnh sửa review
            user = request.user
            if user != review.user:
                return Response({"error": "You do not have permission to update this review."},
                                status=status.HTTP_403_FORBIDDEN)

            # Sử dụng serializer để cập nhật một phần review
            serializer = ReviewSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Review.DoesNotExist:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

     # API xóa review
    # /recruitments_post/pk/delete-review/review_id/
    @action(methods=['delete'], detail=True, url_path='delete-review/(?P<review_id>[^/.]+)', url_name='delete_review')
    def delete_review(self, request, pk=None, review_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy review cần xóa
            review = get_object_or_404(Review, pk=review_id)

            # Kiểm tra xem review có thuộc về bài đăng tuyển dụng không
            if review.recruitment != recruitment_post:
                return Response({"error": "Review does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền xóa review
            if request.user != review.user:
                return Response({"error": "You do not have permission to delete this review."},
                                status=status.HTTP_403_FORBIDDEN)

            # Xóa review
            review.delete()
            return Response({"message": "Review deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Review.DoesNotExist:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)






class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.ListAPIView):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserSerializer
    # Dùng upload ảnh lên Cloud
    parser_classes = [parsers.MultiPartParser, ]
    pagination_class = paginators.UserPagination

    def get_serializer_class(self):
        if self.action == 'create_applicant':
            return serializers.ApplicantCreateSerializer
        if self.action == 'create_employer':
            return serializers.EmployerCreateSerializer
        if self.action == 'patch_current_user':
            return serializers.PatchUserSerializer
        if self.action == 'get_current_user':
            return serializers.UserDetailSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ['get_current_user', 'patch_current_user', 'delete_account']:
            return [perms.IsAdminOrSelf()]
        return [permissions.AllowAny()]

    # API xem chi tiết tài khoản hiện (chỉ xem được của mình) + cập nhật tài khoản (của mình)
    # /users/current-user/
    @action(methods=['get'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        # Đã được chứng thực rồi thì không cần truy vấn nữa => Xác định đây là người dùng luôn
        # user = user hiện đang đăng nhập
        user = request.user

        return Response(serializers.UserDetailSerializer(user).data)

    # API cập nhật một phần cho User
    # /users/<user_id>/patch-current-user/
    @action(methods=['patch'], url_path='patch-current-user', detail=True)
    def patch_current_user(self, request, pk=None):
        # Lấy user từ pk hoặc raise 404 nếu không tìm thấy
        user = get_object_or_404(User, pk=pk)

        serializer = serializers.PatchUserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # API xóa tài khoản
    # /users/<user_id>/delete-account/
    @action(detail=True, methods=['delete'], url_path='delete-account')
    def delete_account(self, request, pk=None):
        try:
            # Lấy user từ pk hoặc raise 404 nếu không tìm thấy
            user = get_object_or_404(User, pk=pk)

            # Kiểm tra quyền hạn: Chỉ người tạo mới có quyền xóa hoặc admin
            if request.user.is_staff or request.user == user:
                user.delete()
                return Response({"message": "User account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "You do not have permission to delete this user account."},
                                status=status.HTTP_403_FORBIDDEN)

        except User.DoesNotExist:
            return Response({"error": "User account not found."}, status=status.HTTP_404_NOT_FOUND)

    # API tạo APPLICANT
    # /users/<user_id>/create_applicant/
    @action(detail=True, methods=['post'], url_path='create_applicant')
    def create_applicant(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        # if not request.user.is_authenticated:  # Nếu không được chứng thực
        #     return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        # if request.user != user and not request.user.is_staff:  # Nếu không phải là admin
        #     return Response({"error": "You do not have permission to create an applicant for this user."},
        #                     status=status.HTTP_403_FORBIDDEN)

        serializer = serializers.ApplicantCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # API tạo EMPLOYER
    # /users/<user_id>/create_employer/
    @action(detail=True, methods=['post'], url_path='create_employer')
    def create_employer(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        # if not request.user.is_authenticated:
        #     return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_employer:
            return Response({"error": "User is not eligible to create an employer."}, status=status.HTTP_403_FORBIDDEN)
        # if request.user != user and not request.user.is_staff:
        #     return Response({"error": "You do not have permission to create an employer for this user."},
        #                     status=status.HTTP_403_FORBIDDEN)

        serializer = serializers.EmployerCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView,
                      generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = Employer.objects.all()
    serializer_class = serializers.EmployerSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.UserPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.EmployerCreateSerializer
        if self.action == 'delete_recruitment_post':
            return serializers.RecruitmentPostSerializer
        if self.action in ['recruitment_posts']:
            return serializers.RecruitmentPostSerializer
        if self.action in ['find_applicants']:
            return serializers.ApplicantSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'recruitment_posts','delete_recruitment_post']:
            return [perms.EmOwnerAuthenticated()]
        elif self.action in ['list']:
            return [perms.AdminIsAuthenticated()]
        elif self.action in ['find_applicants']:
            return [perms.EmIsAuthenticated()]
        return [permissions.IsAuthenticated()]

    # API xuất danh sách bài đăng tuyển dụng do 1 employer tạo ra
    # /employers/{id}/recruitment_posts/
    @action(detail=True, methods=['get'])
    def recruitment_posts(self, request, pk=None):
        employer = get_object_or_404(Employer, pk=pk)

        # Lấy danh sách bài đăng tuyển dụng của nhà tuyển dụng
        recruitment_posts = RecruitmentPost.objects.filter(employer=employer)

        # Phân trang
        paginator = paginators.RecruitmentPostPaginator()
        page = paginator.paginate_queryset(recruitment_posts, request)
        if page is not None:
            serializer = RecruitmentPostSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = RecruitmentPostSerializer(recruitment_posts, many=True)
        return Response(serializer.data)

    # API gợi ý ứng viên phù hợp với bài đăng tuyển dụng cho employer tạo ra
    # /employers/{id}/find_applicants/
    @action(detail=True, methods=['get'])
    def find_applicants(self, request, pk=None):
        employer = get_object_or_404(Employer, pk=pk)
        recruitment_posts = RecruitmentPost.objects.filter(employer=employer)

        # Khởi tạo tập hợp rỗng để lưu ứng viên phù hợp
        matched_applicants = Applicant.objects.none()
        # Duyệt qua từng bài tuyển dụng
        for post in recruitment_posts:
            area = post.area
            career = post.career
            # experience = post.experience
            # salary = post.salary
            applicants = Applicant.objects.filter(
                areas=area,
                career=career,
                # experience__icontains=experience,
                # salary_expectation__icontains=salary
            ).distinct()  # distinct(): Đảm bảo rằng kết quả không có các ứng viên trùng lặp.

            matched_applicants = matched_applicants | applicants

        matched_applicants = matched_applicants.distinct()  # Đảm bảo không có ứng viên trùng lặp

        paginator = paginators.ApplicantPagination()
        page = paginator.paginate_queryset(matched_applicants, request)
        if page is not None:
            serializer = serializers.ApplicantSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = serializers.ApplicantSerializer(matched_applicants, many=True)
        return Response(serializer.data)




class ApplicantViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.UpdateAPIView,
                       generics.DestroyAPIView):
    queryset = Applicant.objects.all()
    serializer_class = serializers.ApplicantSerializer
    # Thiết lập lớp phân trang (pagination class) cho một API view cụ thể.
    # pagination_class = paginators.ApplicantPagination
    pagination_class = paginators.UserPagination

    def get_serializer_class(self):
        if self.action in ['partial_update']:
            return serializers.ApplicantCreateSerializer
        if self.action in ['update']:
            return serializers.ApplicantUpdateSerializer
        if self.action in ['job_recommendations', 'applied_jobs']:
            return serializers.RecruitmentPostSerializer
        return serializers.ApplicantSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'notifications']:
            return [perms.AppOwnerAuthenticated()]
        elif self.action in ['search_applicant']:
            return [perms.EmIsAuthenticated()]
        elif self.action in ['applied_jobs', 'job_recommendations']:
            return [perms.AppIsAuthenticated()]
        elif self.action == 'list':
            return [perms.AdminIsAuthenticated()]
        return [permissions.IsAuthenticated()]

    # Không có endpoint
    # Lấy danh sách ứng viên có kỹ năng là "Python" và "Java":
    # /applicants/?skills=Python&skills=Java
    # Lấy danh sách ứng viên muốn làm việc ở khu vực "quận 3":
    # /applicants/?areas=quan3
    # Lấy danh sách ứng viên có kỹ năng là "Python" và muốn làm việc ở khu vực "Hà Nội":
    # /applicants/?skills=Python&areas=Hanoi
    def get_queryset(self):
        skills = self.request.query_params.getlist('skills')
        areas = self.request.query_params.getlist('areas')
        careers = self.request.query_params.getlist('careers')
        position = self.request.query_params.get('position')

        queryset = Applicant.objects.all()

        if skills:
            # .distinct() trong Django ORM được sử dụng để loại bỏ các bản ghi trùng lặp từ kết quả truy vấn
            queryset = queryset.filter(skills__name__in=skills).distinct()

        if areas:
            queryset = queryset.filter(areas__name__in=areas).distinct()

        if careers:
            queryset = queryset.filter(career__name__in=careers)
        if position:
            queryset = queryset.filter(position__icontains=position)
        return queryset

    # API tìm kiếm ứng viên chỉ bằng các từ liên quan
    # /applicants/search_applicant/?q=
    @action(methods=['get'], detail=False)
    def search_applicant(self, request):
        q = request.query_params.get("q")

        if q:
            skills = Skill.objects.filter(name__icontains=q)
            areas = Area.objects.filter(name__icontains=q)
            careers = Career.objects.filter(name__icontains=q)

            applicants = Applicant.objects.distinct().filter(
                Q(skills__in=skills) | Q(areas__in=areas) | Q(career__in=careers)
            )

            # Sử dụng paginator để phân trang kết quả
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(applicants, request)

            if page is not None:
                serializer = serializers.ApplicantSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = serializers.ApplicantSerializer(applicants, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    # API xem thông báo
    # /applicants/{id}/notifications/
    @action(detail=True, methods=['get'], url_path='notifications')
    def get_notifications(self, request, pk=None):
        user = request.user

        # Kiểm tra xem người dùng là admin hay không => admin thì xuất hết thông báo (sắp theo mới nhất)
        if user.is_staff or user.is_superuser:
            notifications = Notification.objects.all().order_by('-created_date')
            serializer = NotificationSerializer(notifications, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Lấy đối tượng applicant dựa trên pk
        applicant = get_object_or_404(Applicant, pk=pk)

        # Kiểm tra xem user hiện tại có phải là chủ sở hữu của applicant hay không
        if user != applicant.user:
            return Response({'error': 'You do not have permission to view these notifications'},
                            status=status.HTTP_403_FORBIDDEN)

        notifications = Notification.objects.filter(user=applicant.user).order_by(
            '-created_date')  # (sắp theo mới nhất)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # API gợi ý công việc
    # /applicants/{id}/job_recommendations/
    @action(detail=True, methods=['get'])
    def job_recommendations(self, request, pk=None):
        applicant = generics.get_object_or_404(Applicant, pk=pk)
        today = date.today()

        # Query to find matching Recruitment Posts
        queryset = RecruitmentPost.objects.filter(
            # experience__icontains=applicant.experience,
            career=applicant.career,
            # gender=applicant.user.gender,
            # salary__icontains=applicant.salary_expectation,
            area__in=applicant.areas.all(),
            deadline__gte=today  # Chỉ xem xét các bài đăng chưa hết hạn
        ).distinct()

        paginator = paginators.RecruitmentPostPaginator()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = serializers.RecruitmentPostSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = serializers.RecruitmentPostSerializer(queryset, many=True)
        return Response(serializer.data)

    # API applicant đã apply những bài tuyển dụng nào
    # /applicants/{id}/applied_jobs/
    @action(detail=True, methods=['get'])
    def applied_jobs(self, request, pk=None):
        try:
            applicant = generics.get_object_or_404(Applicant, pk=pk)

            # Query to find Job Applications for this applicant
            job_applications = JobApplication.objects.filter(applicant=applicant)
            applied_posts = RecruitmentPost.objects.filter(id__in=job_applications.values('recruitment_id')).distinct()

            # Sử dụng lớp phân trang tùy chỉnh để phân trang danh sách applied_posts
            paginator = paginators.RecruitmentPostPaginator()
            page = paginator.paginate_queryset(applied_posts, request)
            if page is not None:
                serializer = RecruitmentPostSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = RecruitmentPostSerializer(applied_posts, many=True)
            return Response(serializer.data)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "No recruitment posts found."}, status=status.HTTP_404_NOT_FOUND)


# Ai cũng có hể coi khỏi phân quyền
class CareerViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Career.objects.all()
    serializer_class = serializers.CareerSerializer


class EmploymentTypeViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = EmploymentType.objects.all()
    serializer_class = serializers.EmploymentTypeSerializer


class AreaViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Area.objects.all()
    serializer_class = serializers.AreaSerializer


class SkillViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Skill.objects.all()
    serializer_class = serializers.SkillSerializer


from rest_framework.viewsets import ViewSet
from .models import PasswordResetToken
from django.core.mail import send_mail
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()  # Sử dụng mô hình người dùng tùy chỉnh

class PasswordReset(generics.GenericAPIView):
    serializer_class = serializers.EmailSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Chỉ dùng để hiển thị schema, không thay đổi logic
        email = serializer.validated_data["email"]
        print("Email:", email)  # Kiểm tra email có phải là chuỗi không
        user = User.objects.filter(email=email).first()
        if user:
            # encoded_pk = urlsafe_base64_encode(force_bytes(user.pk))
            # token = PasswordResetTokenGenerator().make_token(user)
            token = PasswordResetToken.objects.create(user=user)

            # Gửi email với liên kết đặt lại mật khẩu
            send_mail(
                'Password Reset Request',
                f'''This is the code to change your password: {token.token}
                The code is valid for 5 minutes only.''',  # {token.token} : Sử dụng token thực tế
                'tdmt.lutheir268@gmail.com',
                [email],
                fail_silently=False,
            )


            return Response({'message': 'Code to reset password has been sent to your email'},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'message': 'Password was reset successfully'}, status=status.HTTP_201_CREATED)

class EmailCheckAPIView(generics.GenericAPIView):
    serializer_class = EmailCheckSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return Response({"exists": False}, status=200)
        return Response({"exists": True}, status=200)

class TokenCheckAPIView(generics.GenericAPIView):
    serializer_class = TokenCheckSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return Response({"exists": True}, status=200)
        return Response({"exists": False}, status=200)


# Kiểm tra người dùng đã từng review chưa
class ReviewStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Kiểm tra xem người dùng đã đánh giá bài đăng này chưa
            existing_rating = Review.objects.filter(recruitment=recruitment_post, user=request.user).exists()

            # Sử dụng serializer để trả về kết quả
            serializer = ReviewStatusSerializer({'hasReviewed': existing_rating})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)


# class ChatListCreateView(generics.ListCreateAPIView):
#     serializer_class = ChatSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#
#         # Kiểm tra xem user là applicant hay employer
#         applicant = Applicant.objects.filter(user=user).first()
#         employer = Employer.objects.filter(user=user).first()
#
#         # Lọc các chat dựa trên việc user là applicant hay employer
#         if applicant:
#             return Chat.objects.filter(applicant=applicant)
#         elif employer:
#             return Chat.objects.filter(employer=employer)
#         else:
#             return Chat.objects.none()  # Trả về rỗng nếu không phải applicant hay employer


# class MessageCreateView(generics.CreateAPIView):
#     serializer_class = MessageSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def perform_create(self, serializer):
#         # Lấy chat từ id trong URL
#         chat = Chat.objects.get(id=self.kwargs['chat_id'])
#
#         # Lưu tin nhắn, xác định sender là người dùng hiện tại
#         serializer.save(chat=chat, sender=self.request.user)

from jobs.utils import google_callback
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from oauth2_provider.models import AccessToken, Application
from oauthlib.common import generate_token
from jobs.utils import  upload_image_from_url
from datetime import timedelta
from django.shortcuts import redirect
import requests
# Đăng nhập với Google
# class GoogleOAuth2LoginCallbackView(APIView):
#     def get(self, request):
#         redirect_uri = request.build_absolute_uri(reverse("google_login_callback"))
#         auth_uri = request.build_absolute_uri()
#
#         user_data = google_callback(redirect_uri, auth_uri)
#
#         # Lấy URL frontend từ OAuth state
#         frontend_url = request.GET.get('state')
#
#         if frontend_url is None:
#             return JsonResponse({"error": "State (frontend URL) is missing."}, status=400)
#
#         user_picture = user_data.get('picture')
#
#         user, _ = User.objects.get_or_create(
#             username=user_data["email"],
#             defaults={"first_name": user_data["given_name"],
#                       "last_name": user_data.get("family_name", ""),
#                       'email': user_data["email"],
#                       "is_employer": False,
#                       'avatar': upload_image_from_url(user_picture)
#                       }
#
#         )
#
#         # Populate the extended user data stored in UserProfile.
#         UserProfile.objects.get_or_create(
#             user=user, defaults={"google_id": user_data["id"]}
#         )
#         expires = timezone.now() + timedelta(seconds=36000)
#         access_token = AccessToken.objects.create(
#             user=user,
#             scope='read write',
#             expires=expires,
#             token=generate_token(),
#             application=get_object_or_404(Application, name="hotel")
#         )
#
#         # Create the auth token for the frontend to use.
#         token, _ = Token.objects.get_or_create(user=user)
#         # print(access_token.token)
#         # Here we assume that once we are logged in we should send
#         # a token to the frontend that a framework like React or Angular
#         # can use to authenticate further requests.
#         # return JsonResponse({"token": token.key})
#         # Chuyển hướng về frontend với token trong query parameters
#         redirect_url = f"{frontend_url}/?token={access_token.token}"
#         return redirect(redirect_url)

class GoogleOAuth2LoginCallbackView(APIView):
    def get(self, request):
        redirect_uri = request.build_absolute_uri(reverse("google_login_callback"))
        auth_uri = request.build_absolute_uri()

        user_data = google_callback(redirect_uri, auth_uri)

        # Lấy URL frontend từ OAuth state
        frontend_url = request.GET.get('state')

        if frontend_url is None:
            return JsonResponse({"error": "State (frontend URL) is missing."}, status=400)

        user_picture = user_data.get('picture')

        user, _ = User.objects.get_or_create(
            username=user_data["email"],
            defaults={"first_name": user_data["given_name"],
                      "last_name": user_data.get("family_name", ""),
                      'email': user_data["email"],
                      "is_employer": False,
                      'avatar': upload_image_from_url(user_picture)
                      }

        )

        # Populate the extended user data stored in UserProfile.
        UserProfile.objects.get_or_create(
            user=user, defaults={"google_id": user_data["id"]}
        )
        expires = timezone.now() + timedelta(seconds=36000)
        access_token = AccessToken.objects.create(
            user=user,
            scope='read write',
            expires=expires,
            token=generate_token(),
            application=get_object_or_404(Application, name="hotel")
        )

        # Create the auth token for the frontend to use.
        token, _ = Token.objects.get_or_create(user=user)
        # print(access_token.token)
        # Here we assume that once we are logged in we should send
        # a token to the frontend that a framework like React or Angular
        # can use to authenticate further requests.
        # return JsonResponse({"token": token.key})
        # Chuyển hướng về frontend với token trong query parameters
        redirect_url = f"{frontend_url}/?token={access_token.token}"
        return redirect(redirect_url)


# class FacebookLoginCallbackView(APIView):
#     def post(self, request):
#         access_token = request.data.get('accessToken')
#         print(access_token)
#         if not access_token:
#             return Response({'error': 'Access token not provided'}, status=status.HTTP_400_BAD_REQUEST)

#         facebook_url = f'https://graph.facebook.com/me?access_token={access_token}&fields=id,name,email,picture'

#         response = requests.get(facebook_url)
#         if response.status_code != 200:
#             return Response({'error': 'Invalid access token'}, status=status.HTTP_400_BAD_REQUEST)

#         user_data = response.json()
#         user_email = user_data.get('email')
#         user_name = user_data.get('name')
#         user_picture = user_data.get('picture', {}).get('data', {}).get('url')

#         if not user_email:
#             return Response({'error': 'Email not found in access token'}, status=status.HTTP_400_BAD_REQUEST)

#         user, created = User.objects.get_or_create(
#             username=user_name,
#             defaults={'first_name': user_name, 'email': user_email, "is_employer": False,
#                       'avatar': upload_image_from_url(user_picture)})

#         # Cập nhật thông tin mở rộng trong UserProfile
#         UserProfile.objects.get_or_create(
#             user=user, defaults={"facebook_id": user_data["id"]}
#         )

#         # access_token, refresh_token = utils.create_user_token(user=user)
#         # Tạo Access Token
#         expires = timezone.now() + timedelta(seconds=36000)
#         access_token = AccessToken.objects.create(
#             user=user,
#             scope='read write',
#             expires=expires,
#             token=generate_token(),
#             application=get_object_or_404(Application, name="hotel")
#         )

#         return Response({
#                 'access_token': access_token.token,
#         })

# API Tạo phòng Chat
# /chat/create_or_get_chat/
@api_view(['POST'])
def create_or_get_chat(request):
    applicant_id = request.data.get('applicant_id')
    post_id = request.data.get('post_id')

    if not applicant_id or not post_id:
        return Response({'error': 'Applicant ID and Post ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Lấy applicant từ database
    applicant = get_object_or_404(Applicant, id=applicant_id)

    # Lấy post từ database và kiểm tra employer của post đó
    post = get_object_or_404(RecruitmentPost, id=post_id)
    employer = post.employer

    # Kiểm tra nếu phòng chat đã tồn tại giữa applicant và employer
    chat, created = Chat.objects.get_or_create(applicant=applicant, employer=employer)

    return Response({'chat_id': chat.id, 'created': created})

# Request Body:
# {
#     "applicant_id": 1,
#     "post_id": 2
# }

# Response
# {
#     "chat_id": 3,
#     "created": true
# }
# true : tạo phòng chat mới / false : phòng chat đã tồn tại


# API Lấy Danh Sách Tin Nhắn trong Phòng Chat
# /chat/<chat_id>/messages/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_messages(request, chat_id):
    user = request.user
    try:
        chat = Chat.objects.get(id=chat_id)

        # Kiểm tra xem người dùng có quyền truy cập chat này không
        if hasattr(user, 'employer'):
            if chat.employer.user != user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        elif hasattr(user, 'applicant'):
            if chat.applicant.user != user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'User is neither employer nor applicant'}, status=status.HTTP_403_FORBIDDEN)

        # Sắp xếp tin nhắn theo thứ tự cũ nhất đến mới nhất
        messages = Message.objects.filter(chat=chat).order_by('created_at')
        message_data = [
            {
                'id': message.id,
                'text': message.text,
                'sender_username': message.sender.username,
                'created_at': message.created_at
            }
            for message in messages
        ]
        return Response(message_data)
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)

# API Gửi Tin Nhắn
# /chat/send_message/<chat_id>/
@api_view(['POST'])
def send_message(request, chat_id):
    user = request.user
    text = request.data.get('text')

    if not text:
        return Response({'error': 'Message text is required.'}, status=status.HTTP_400_BAD_REQUEST)

    chat = get_object_or_404(Chat, id=chat_id)

    # Kiểm tra xem người dùng có thuộc phòng chat này hay không
    if not (user == chat.applicant.user or user == chat.employer.user):
        return Response({'error': 'You do not have permission to send messages in this chat.'},
                        status=status.HTTP_403_FORBIDDEN)

    message = Message.objects.create(chat=chat, sender=user, text=text)

    return Response({'message': 'Message sent successfully.'}, status=status.HTTP_201_CREATED)

# Request Body
# {
#     "text": "Hello, I have a question about this position."
# }

# Response:
# {
#     "message": "Message sent successfully."
# }

# API Danh sách phòng Chat của Employer
# /chats/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employer_chats(request):
    user = request.user
    try:
        employer = Employer.objects.get(user=user)
    except Employer.DoesNotExist:
        return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)

    # Lấy danh sách phòng chat mà employer tham gia
    chats = Chat.objects.filter(employer=employer).prefetch_related('messages', 'applicant__user')
    chat_data = [
        {
            'id': chat.id,
            'applicant_username': chat.applicant.user.username,
            'applicant_avatar': chat.applicant.user.avatar.url if chat.applicant.user.avatar else None,
            'lastMessage': chat.messages.last().text if chat.messages.exists() else '',
            'lastMessageTime': chat.messages.last().created_at if chat.messages.exists() else chat.created_at,
        }
        for chat in chats
    ]

    return Response(chat_data)

# Danh sách phòng chat của Applicant
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_applicant_chats(request):
    user = request.user
    try:
        applicant = Applicant.objects.get(user=user)
    except Applicant.DoesNotExist:
        return Response({'error': 'User is not an applicant'}, status=status.HTTP_403_FORBIDDEN)

    # Lấy danh sách phòng chat mà applicant tham gia
    chats = Chat.objects.filter(applicant=applicant).prefetch_related('messages', 'employer__user')
    chat_data = [
        {
            'id': chat.id,
            'employer_username': chat.employer.user.username,
            'employer_avatar': chat.employer.user.avatar.url if chat.employer.user.avatar else None,
            'lastMessage': chat.messages.last().text if chat.messages.exists() else '',
            'lastMessageTime': chat.messages.last().created_at if chat.messages.exists() else chat.created_at,
        }
        for chat in chats
    ]

    return Response(chat_data, status=status.HTTP_200_OK)


# API lấy danh sách đơn ứng tuyển của Applicant
class ApplicantJobApplicationsListView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ApplicantPagination
    def get_queryset(self):
        # Lấy Applicant dựa trên user đã đăng nhập
        applicant = self.request.user.applicant
        return JobApplication.objects.filter(applicant=applicant).order_by('-date')


# API danh sách việc làm gợi ý cho Applicant
class RecommendedJobsView(generics.ListAPIView):
    serializer_class = RecruitmentPostSerializer
    pagination_class = RecruitmentPostPaginator
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        applicant = Applicant.objects.get(user=self.request.user)
        queryset = RecruitmentPost.objects.all()

        # Lọc các bài tuyển dụng phù hợp với thông tin của Applicant
        queryset = queryset.filter(
            career=applicant.career,
            # area__in=applicant.areas.all(),
            # salary__gte=applicant.salary_expectation,
            # experience__icontains=applicant.experience
        )

        return queryset


# API danh sách bài đăng tuyển dụng mà Employer đã tạo ra
class EmployerRecruitmentPostViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecruitmentPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.employer:
            return RecruitmentPost.objects.filter(employer__user=user)
        return RecruitmentPost.objects.none()

from django_filters.rest_framework import DjangoFilterBackend
# API tìm kiếm ứng viên (Applicant)
class FindApplicantViewSet(viewsets.ModelViewSet):
    queryset = Applicant.objects.all()
    serializer_class = ViewApplicantSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'position', 'skills__name', 'areas__name', 'career__name']
    ordering_fields = ['user__username', 'salary_expectation']

    @action(detail=False, methods=['get'])
    def search(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        min_salary = request.query_params.get('min_salary')
        max_salary = request.query_params.get('max_salary')

        if min_salary:
            queryset = queryset.filter(salary_expectation__gte=int(min_salary))
        if max_salary:
            queryset = queryset.filter(salary_expectation__lte=int(max_salary))

        skills = request.query_params.get('skills')
        if skills:
            skill_list = skills.split(',')
            queryset = queryset.filter(skills__name__in=skill_list).distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


#  API Danh sách đơn apply bài đăng tuyển dụng
class ListApplicationsForPost(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        try:
            employer = request.user.employer
            post = RecruitmentPost.objects.get(id=post_id, employer=employer)
            applications = JobApplication.objects.filter(recruitment=post)
            serializer = JobApplicationSerializer(applications, many=True)
            return Response(serializer.data, status=200)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Bài đăng không tồn tại"}, status=404)


# @api_view(['PATCH'])
# @permission_classes([permissions.IsAuthenticated])
# def update_application_status(request, application_id):
#     try:
#         # Lấy đơn ứng tuyển theo ID
#         application = Application.objects.get(id=application_id)
#
#         # Kiểm tra xem employer có quyền thay đổi trạng thái không
#         if application.recruitment.employer != request.user:
#             return Response(
#                 {"detail": "Bạn không có quyền cập nhật đơn ứng tuyển này."},
#                 status=status.HTTP_403_FORBIDDEN
#             )
#
#         # Kiểm tra và cập nhật trạng thái
#         serializer = JobApplicationStatusSerializer(application, data=request.data, partial=True)
#         if serializer.is_valid():
#             updated_application = serializer.save()
#             return Response(
#                 {
#                     "detail": "Cập nhật trạng thái đơn ứng tuyển thành công.",
#                     "application": serializer.data
#                 },
#                 status=status.HTTP_200_OK
#             )
#
#         return Response(
#             {
#                 "detail": "Dữ liệu không hợp lệ.",
#                 "errors": serializer.errors
#             },
#             status=status.HTTP_400_BAD_REQUEST
#         )
#
#     except Application.DoesNotExist:
#         return Response(
#             {"detail": "Không tìm thấy đơn ứng tuyển."},
#             status=status.HTTP_404_NOT_FOUND
#         )


class JobApplicationStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, pk):
        try:
            # Lấy đối tượng JobApplication dựa trên primary key (pk)
            job_application = JobApplication.objects.get(pk=pk)
        except JobApplication.DoesNotExist:
            return Response({'error': 'Không tìm thấy đơn xin việc'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize và cập nhật status
        serializer = JobApplicationStatusSerializer(job_application, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Cập nhật trạng thái thành công'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from jobPortal import settings

class EmployerRegistrationView(APIView):
    def post(self, request):
        serializer = RegistereEmployerSerializer(data=request.data)
        if serializer.is_valid():
            employer = serializer.save()

            # Prepare notification
            subject = 'New Employer Registration Notification'
            message = f'''Request to create an employer account:
            - UserID: {employer.id}
            - Username: {employer.username}
            - Email: {employer.email}
            - Registration Time: {timezone.now()}
            '''

            # Send email notification to admin or the system
            send_mail(
                subject,
                message,
                'tdmt.lutheir268@gmail.com',  # Email hệ thống đăng ký làm email gửi đi đến khách hàng
                ['2151050455tien@ou.edu.vn'],  # Email hệ thống nhận và xử lý
                fail_silently=False,
            )


            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from dotenv import load_dotenv
from django.db import transaction

load_dotenv()
import stripe

stripe.api_key = os.environ.get('STRIPE_TEST_SECRET_KEY')
class StripeCheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]  # Chỉ cho phép người dùng đã xác thực

    def create(self, request):

        try:
            # Lấy price_id từ request body
            price_id = request.data.get('price_id')
            product_item = request.data.get('product_item')

            if not price_id:
                return Response({"error": "Price ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Tạo session thanh toán với price_id được gửi từ front-end
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                payment_method_types=['card'],
                mode='payment',
                success_url=settings.SITE_URL + '/payment_success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_URL + '?canceled=true',
            )

            # # Lưu session với trạng thái pending
            # invoice = Invoice(
            #     user=request.user,
            #     stripe_session_id=checkout_session.id,
            #     amount_total=10.00,
            #     currency='USD',
            #     payment_status='pending',
            #     product_item=product_item,
            #     customer_email = request.user.email,  # Lưu email người dùng
            #     payment_date = timezone.now(),  # Lưu ngày thanh toán hiện tại
            # )
            # Sử dụng session để lưu thông tin tạm thời
            request.session['pending_payment'] = {
                'session_id': checkout_session.id,
                'product_item': product_item,
            }
            request.session.modified = True
            # invoice.save()

            return Response({
                "url": checkout_session.url,
                "session_id": checkout_session.id  # Thêm session_id vào phản hồi
            }, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': 'Something went wrong: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def retrieve_payment(self, request):
        session_id = request.GET.get('session_id')

        if not session_id:
            return Response({"error": "Session ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Kiểm tra xem hóa đơn đã tồn tại chưa
                existing_invoice = Invoice.objects.filter(stripe_session_id=session_id).first()
                if existing_invoice:
                    return Response(self.serialize_invoice(existing_invoice), status=status.HTTP_200_OK)

                checkout_session = stripe.checkout.Session.retrieve(session_id)

                if checkout_session.payment_status == 'paid':
                    invoice = Invoice(
                        user=request.user,
                        stripe_session_id=session_id,
                        amount_total=checkout_session.amount_total / 100,
                        currency=checkout_session.currency,
                        payment_status='success',
                        product_item=request.session.get('pending_payment', {}).get('product_item'),
                        customer_email=checkout_session.customer_details.email,
                        payment_date=timezone.now(),
                    )
                    invoice.save()

                    # Xóa thông tin tạm thời
                    request.session.pop('pending_payment', None)

                    return Response(self.serialize_invoice(invoice), status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Payment not completed."}, status=status.HTTP_400_BAD_REQUEST)

        except ObjectDoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def serialize_invoice(invoice):
        return {
            "session_id": invoice.stripe_session_id,
            "amount_total": str(invoice.amount_total),
            "currency": invoice.currency,
            "payment_status": invoice.payment_status,
            "payment_date": invoice.payment_date.isoformat(),
            "customer_email": invoice.customer_email,
            "product_item": invoice.product_item,
        }

    def list_invoices(self, request):
        try:
            # Lấy người dùng hiện tại từ request
            user = request.user

            # Lấy danh sách các hóa đơn của người dùng
            invoices = Invoice.objects.filter(user=user)

            # Chuyển đổi các hóa đơn thành dạng JSON để trả về
            invoice_list = []
            for invoice in invoices:
                invoice_list.append({
                    "session_id": invoice.stripe_session_id,
                    "amount_total": str(invoice.amount_total),
                    "currency": invoice.currency,
                    "payment_status": invoice.payment_status,
                    "payment_date": invoice.payment_date,
                    "customer_email": invoice.customer_email,
                    "product_item": invoice.product_item,
                })

            # Trả về danh sách hóa đơn dưới dạng JSON
            return Response({"invoices": invoice_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
