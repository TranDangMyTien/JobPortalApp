from django.contrib.auth import get_user_model

from jobs.models import RecruitmentPost, Comment, Rating
from jobs import serializers
from jobs import paginators
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import viewsets, generics, permissions, status, parsers
from rest_framework.decorators import action
from jobs import dao
from .models import JobApplication, Employer, Applicant, User, Notification, Status, Like
from .serializers import (JobApplicationSerializer, AuthenticatedRecruitmentPostSerializer, CreatRatingSerializer,
                          ReadCommentSerializer, Career, EmploymentType, Area, CreateCommentReplySerializer,
                          RecruitmentPostSerializer, NotificationSerializer, Skill, CreateCommentSerializer,
                          CreateJobApplicationStatusSerializer)
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .filters import RecruitmentPostFilter
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date
from jobs import perms


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

class RecruitmentPostViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.ListAPIView, generics.CreateAPIView,
                             generics.UpdateAPIView):
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
        if self.action in ['create_comment', 'read_comments', 'partial_update_comment', 'delete_comment']:
            return serializers.CreateCommentSerializer
        if self.action in ['read_comments']:
            return serializers.ReadCommentSerializer
        if self.action in ['reply_comment', 'partial_update_reply', 'delete_reply']:
            return serializers.CreateCommentReplySerializer
        if self.action in ['read_reply_comment']:
            return serializers.CommentSerializer
        if self.action in ['create', 'partial_update', 'update']:
            return serializers.CreateRecruitmentPostSerializer
        if self.action in ['read_rating', 'create_rating', 'partial_update_rating', 'delete_rating']:
            return serializers.CreatRatingSerializer
        if self.action in ['list_apply', 'view_application']:
            return serializers.JobApplicationSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ['create_comment', 'reply_comment', 'report', 'create_rating', 'like', 'apply']:
            return [permissions.IsAuthenticated()]
        if self.action in ['create']:
            return [perms.EmIsAuthenticated()]
        if self.action in ['partial_update', 'update']:
            return [perms.EmOwnerAuthenticated()]
        if self.action in [
            'num_applications', 'hide_post', 'count_likes', 'partial_update_application',
            'delete_application', 'partial_update_rating', 'delete_rating',
            'delete_comment', 'delete_reply', 'partial_update_comment',
            'partial_update_reply'
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
    @action(detail=True, methods=['post'])
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
    # /recruitments_post/<pk>/ratings/
    @action(methods=['get', 'post'], detail=True, url_path='ratings', url_name='ratings')
    def create_rating(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Kiểm tra xem người dùng đã đánh giá bài đăng này chưa
            existing_rating = Rating.objects.filter(recruitment=recruitment_post, user=request.user).first()
            if existing_rating:
                return Response({"error": "You have already rated this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            rating_data = {
                'recruitment_post': recruitment_post.id,
                'rating': request.data.get('rating'),
                'user': request.user.id
            }

            serializer = CreatRatingSerializer(data=rating_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Trả về thông tin về đánh giá mới được tạo
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xem chi tiết đánh giá một bài tuyển dụng
    # /recruitments_post/<pk>/ratings/
    @action(methods=['get'], detail=True, url_path='ratings', url_name='ratings')
    def read_rating(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy danh sách rating của bài đăng
            ratings = recruitment_post.rating_set.all()

            # Phân trang danh sách rating (commented out)
            # paginator = paginators.RatingPaginator()
            # paginated_ratings = paginator.paginate_queryset(ratings, request)

            # Serialize danh sách rating
            # serializer = CreatRatingSerializer(paginated_ratings, many=True)  # Sử dụng phân trang
            serializer = CreatRatingSerializer(ratings, many=True)  # Không sử dụng phân trang

            # Trả về danh sách rating đã phân trang (commented out)
            # return paginator.get_paginated_response(serializer.data)

            # Trả về danh sách rating không phân trang
            return Response(serializer.data, status=status.HTTP_200_OK)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API cập nhật rating một bài đăng tuyển dụng
    # /recruitments_post/{pk}/ratings/{rating_id}/partial-update/
    @action(detail=True, methods=['patch'], url_path='ratings/(?P<rating_id>\d+)/partial-update')
    def partial_update_rating(self, request, pk=None, rating_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)
            # Lấy comment từ comment_id
            rating = get_object_or_404(Rating, pk=rating_id)
            # Kiểm tra xem comment có thuộc về bài đăng tuyển dụng không
            if rating.recruitment != recruitment_post:
                return Response({"error": "Rating does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)
            # Kiểm tra quyền chỉnh sửa Rating
            user = request.user
            if user != rating.user:
                return Response({"error": "You do not have permission to delete this rating."},
                                status=status.HTTP_403_FORBIDDEN)

            # Cập nhật một phần của rating
            for key, value in request.data.items():
                setattr(rating, key, value)
            rating.save()
            # Serialize và trả về thông tin cập nhật của rating
            serializer = CreatRatingSerializer(rating)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Rating.DoesNotExist:
            return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xóa rating của một bài đăng tuyển dụng
    # /recruitments_post/<pk>/ratings/<rating_id>/delete/
    @action(detail=True, methods=['delete'], url_path='ratings/(?P<rating_id>\d+)/delete',
            url_name='delete_rating')
    def delete_rating(self, request, pk=None, rating_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy rating từ rating_id
            rating = get_object_or_404(Rating, pk=rating_id)

            # Kiểm tra xem rating có thuộc về bài đăng tuyển dụng không
            if rating.recruitment_post != recruitment_post:
                return Response({"error": "Rating does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền xóa rating
            user = request.user
            if user != rating.user:
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            # Xóa rating
            rating.delete()

            return Response({"message": "Rating deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Rating.DoesNotExist:
            return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)

    # API tạo mới một comment trong bài đăng tuyển dụng + Xem danh sách comment của bài đăng tuyển dụng
    # /recruitments_post/<pk>/comments/
    # /recruitments_post/<pk>/comments/<userId>/user/
    @action(methods=['post'], detail=True, url_path=r'comments/(?P<userId>\d+)/user', url_name='comments_user')
    def create_comment(self, request, pk=None, userId=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = RecruitmentPost.objects.get(pk=pk)

            # Lấy người dùng từ userId
            user = User.objects.get(pk=userId)

            if user:
                comment = Comment.objects.create(
                    user=user,
                    content=request.data.get('content'),
                    recruitment=recruitment_post,
                    created_date=timezone.now()
                )
                serializer = CreateCommentSerializer(comment)

                # Trả về thông tin về comment mới được tạo
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "User not found."},
                                status=status.HTTP_400_BAD_REQUEST)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # API xem danh sách comment của một bài đăng tuyển dụng
    # /recruitments_post/<pk>/read-comments/
    @action(methods=['get'], detail=True, name='read-comments', url_path='read-comments', url_name='read-comments')
    def read_comments(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = RecruitmentPost.objects.get(pk=pk)
            # Lấy danh sách comment của bài đăng
            comments = recruitment_post.comment_set.all()

            # Phân trang danh sách comment
            # paginator = paginators.CommentPaginator()
            # paginated_comments = paginator.paginate_queryset(comments, request)

            # # Serialize danh sách comment
            # serializer = CreateCommentSerializer(paginated_comments, many=True)

            # Serialize danh sách comment
            serializer = ReadCommentSerializer(comments, many=True)

            # # Trả về danh sách comment đã phân trang
            # return paginator.get_paginated_response(serializer.data)

            # Trả về danh sách comment đã serialize
            return Response(serializer.data)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API reply commment trong một bài tuyển dụng nhất định
    # /recruitments_post/<pk>/comments/<comment_pk>/reply_comment/
    @action(detail=True, methods=['post'], url_path='comments/(?P<comment_pk>\d+)/reply_comment',
            url_name='reply_comment')
    def reply_comment(self, request, pk=None, comment_pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = RecruitmentPost.objects.get(pk=pk)
            # Lấy comment cha từ comment_pk
            parent_comment = Comment.objects.get(pk=comment_pk)
            # Tạo một comment mới
            user = request.user

            if user:
                reply_comment = Comment.objects.create(
                    recruitment=recruitment_post,
                    content=request.data.get('content'),
                    parent=parent_comment,
                    **{user.__class__.__name__.lower(): user}  # UNPACK để tạo keyword
                )
                serializer = CreateCommentSerializer(reply_comment)
                # Trả về thông tin về reply comment mới được tạo
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "User is not an applicant or employer."},
                                status=status.HTTP_400_BAD_REQUEST)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

    # API đọc danh sách reply comment
    # /recruitments_post/<pk>/comments/<comment_pk>/reply_comment/
    @action(detail=True, methods=['get'], url_path='comments/(?P<comment_pk>\d+)/read_reply_comment',
            url_name='read_reply_comment')
    def read_reply_comment(self, request, pk=None, comment_pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = RecruitmentPost.objects.get(pk=pk)
            # Lấy comment cha từ comment_pk
            parent_comment = Comment.objects.get(pk=comment_pk, recruitment_id=recruitment_post.id)
            # Lấy danh sách các reply comment cho comment cha
            replies = parent_comment.replies.all()  # replies: là một trường related_name
            # Phân trang danh sách reply comment
            paginator = paginators.CommentReplyPaginator()
            paginated_replies = paginator.paginate_queryset(replies, request)
            # Serialize danh sách reply comment
            serializer = CreateCommentReplySerializer(paginated_replies, many=True)
            # Trả về danh sách comment đã phân trang
            return paginator.get_paginated_response(serializer.data)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xóa comment trong bài đăng tuyển dụng => Xóa luôn các comment là con
    # /recruitments_post/<pk>/comments/<comment_id>/delete/
    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>\\d+)/delete', url_name='delete_comment')
    def delete_comment(self, request, pk=None, comment_id=None):
        try:
            recruitment_post = RecruitmentPost.objects.get(pk=pk)
            comment = Comment.objects.get(pk=comment_id)

            if comment.recruitment != recruitment_post:
                return Response({"error": "Comment does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            if user != comment.user:  # Chỉ người tạo mới được xóa
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            comment.delete()
            return Response({"message": "Comment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xóa comment reply trong bài đăng tuyển dụng
    # /recruitments_post/<pk>/comments/<comment_id>/replies/<reply_id>/delete/
    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>\d+)/replies/(?P<reply_id>\d+)/delete',
            url_name='delete_reply')
    def delete_reply(self, request, pk=None, comment_id=None, reply_id=None):
        try:
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)
            comment = get_object_or_404(Comment, pk=comment_id)
            reply = get_object_or_404(Comment, pk=reply_id, parent=comment)

            if comment.recruitment != recruitment_post:
                return Response({"error": "Comment does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            if user != comment.user:
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            reply.delete()
            return Response({"message": "Reply deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment or reply not found."}, status=status.HTTP_404_NOT_FOUND)

    # API cập nhật một phần comment trong bài đăng tuyển dụng
    # /recruitments_post/{pk}/comments/{comment_id}/partial-update/
    @action(detail=True, methods=['patch'], url_path='comments/(?P<comment_id>\d+)/partial-update',
            url_name='partial_update_comment')
    def partial_update_comment(self, request, pk=None, comment_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Lấy comment từ comment_id
            comment = get_object_or_404(Comment, pk=comment_id)

            # Kiểm tra xem comment có thuộc về bài đăng tuyển dụng không
            if comment.recruitment != recruitment_post:
                return Response({"error": "Comment does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            if user != comment.user:
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            # Cập nhật một phần của comment
            for key, value in request.data.items():
                setattr(comment, key, value)
            comment.save()

            return Response(CreateCommentSerializer(comment).data, status=status.HTTP_200_OK)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

    # API cập nhật một phần comment reply trong bài đăng tuyển dụng
    # /recruitments_post/<pk>/comments/<comment_id>/replies/<reply_id>/partial-update/
    @action(detail=True, methods=['patch'],
            url_path='comments/(?P<comment_id>\d+)/replies/(?P<reply_id>\d+)/partial-update',
            url_name='partial_update_reply')
    def partial_update_reply(self, request, pk=None, comment_id=None, reply_id=None):
        try:
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)
            comment = get_object_or_404(Comment, pk=comment_id)
            reply = get_object_or_404(Comment, pk=reply_id, parent=comment)

            if comment.recruitment != recruitment_post:
                return Response({"error": "Comment does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            if user != comment.user:
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            for key, value in request.data.items():
                setattr(reply, key, value)
            reply.save()

            return Response(CreateCommentReplySerializer(reply).data, status=status.HTTP_200_OK)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment or reply not found."}, status=status.HTTP_404_NOT_FOUND)


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

    # API xóa bài đăng tuyển dụng
    # /employers/{employer_id}/recruitment_posts/{post_id}/delete/
    @action(detail=True, methods=['delete'], url_path='recruitment_posts/(?P<post_id>[^/.]+)/delete')
    def delete_recruitment_post(self, request, pk=None, post_id=None):
        employer = get_object_or_404(Employer, pk=pk)
        recruitment_post = get_object_or_404(RecruitmentPost, pk=post_id, employer=employer)

        # Đảm bảo người dùng thực hiện yêu cầu là chủ sở hữu của bài đăng tuyển dụng
        if recruitment_post.employer.user != request.user:
            return Response({'detail': 'You do not have permission to delete this post.'},
                            status=status.HTTP_403_FORBIDDEN)

        recruitment_post.delete()
        return Response({'detail': 'Recruitment post deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


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
