from jobs.models import RecruitmentPost, Comment, Rating
from jobs import serializers, filters
from jobs import paginators
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import viewsets, generics, permissions, status, parsers
from rest_framework.decorators import action
from jobs import dao
from .models import JobApplication, Employer, Applicant, User
from .serializers import JobApplicationSerializer, RatingSerializer, CommentSerializer, RecruitmentPostSerializer
from django.shortcuts import get_object_or_404
from datetime import datetime
from .filters import RecruitmentPostFilter
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.
# Làm việc với GenericViewSet
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

class RecruitmentPostViewSet(viewsets.ModelViewSet):
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



    # # PHẦN LỌC DỮ LIỆU
    # def get_queryset(self):
    #     # queries = self.queryset: Gán self.queryset cho biến queries. self.queryset
    #     # chứa tất cả các bài đăng tuyển dụng có trạng thái active=True.
    #     queries = self.queryset
    #
    #     # LỌC CÁC BÀI ĐĂNG TUYỂN HẾT THỜI HẠN
    #     # Vòng lặp for q in queries: Duyệt qua mỗi đối tượng RecruitmentPost trong queries
    #     for q in queries:
    #         #  Kiểm tra xem ngày hết hạn của RecruitmentPost (q.deadline) có nhỏ hơn hoặc bằng ngày hiện tại không.
    #         # Điều này đảm bảo rằng chỉ có các bài đăng tuyển dụng đã hết hạn sẽ bị vô hiệu hóa.
    #         if q.deadline <= timezone.now().date():
    #             #  Đặt thuộc tính active của bài đăng tuyển dụng (RecruitmentPost) thành False,
    #             #  ngăn chặn nó khỏi hiển thị trong các kết quả tìm kiếm hoặc các yêu cầu khác.
    #             q.active = False
    #             # Lưu thay đổi vào cơ sở dữ liệu.
    #             q.save()
    #         # Lọc các bài đăng đã hết hạn khỏi queries
    #         queries = queries.filter(active=True)
    #
    #     # PHẦN KIỀM KIẾM
    #     if self.action.__eq__('list'):
    #         title = self.request.query_params.get('title')
    #         # Nếu q khác null có nghĩa là truy vấn
    #         if title:
    #             # recruitments_post/?tile=
    #             queries = queries.filter(title__icontains=title)
    #
    #         employer = self.request.query_params.get('employer_id')
    #         if employer:
    #             # Dùng employer__id: thì nó join 2 bảng lại với nhau
    #             # Ví dụ tìm 10 lần tìm thì nó join lại 10 lần => Tốn chi phí và thời gian
    #             # Nên dùng employer_id vì nó được chương trình sinh ra sẵn cho khóa ngoại của mỗi bảng
    #             # Ở class RecruitmentPost có trường khóa ngoại employer => Django sinh ra 1 trường mới là employer_id
    #             # /recruitments_post/?employer_id=
    #             queries = queries.filter(employer_id=employer)
    #
    #         career = self.request.query_params.get('career')
    #         if career:
    #             # /recruitments_post/?career=
    #             queries = queries.filter(career__name__icontains=career)
    #
    #         employment_type = self.request.query_params.get('employment_type')
    #         if employment_type:
    #             # /recruitments_post/?employment_type=
    #             queries = queries.filter(employmenttype__type__icontains=employment_type)
    #
    #         location = self.request.query_params.get('location')
    #         if location:
    #             # /recruitments_post/?location=
    #             queries = queries.filter(location__icontains=location)
    #
    #     page = self.paginate_queryset(queries)  # Phương thức trong DRF -> thực hiện phân trang cho một QuerySet (queries).
    #     # Phương thức này sẽ cắt nhỏ queries thành các trang, với số lượng kết quả trên mỗi trang được xác định
    #     # bởi thuộc tính pagination_class của view.
    #     if page is not None:
    #         # self.get_serializer phương thức để lấy một serializer instance dựa trên serializer_class
    #         # đã định nghĩa trong view
    #         # serializer sẽ được khởi tạo với page object, đại diện cho tập hợp các kết quả của trang hiện tại.
    #         # Tham số many=True  cho biết rằng dữ liệu đầu vào cho serializer là một tập hợp các object
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #     # Trả về queries sau khi đã thực hiện các thay đổi
    #     return queries

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

        return queries


    # API lọc bài tuyển dụng theo mức lương
    # /recruitments_post/filter_salary/?min_salary=5000000 => bài đăng có mức lương từ 5,000,000 VND trở lên
    # /recruitments_post/filter_salary/?max_salary=10000000 => bài đăng có mức lương dưới 10,000,000 VND
    # /recruitments_post/filter_salary/?min_salary=5000000&max_salary=10000000
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
            # Phân trang cho danh sách bài đăng
            paginator = self.pagination_class()
            paginated_recruitment_posts = paginator.paginate_queryset(recruitment_posts, request)

            serializer = serializers.RecruitmentPostSerializer(paginated_recruitment_posts, many=True)
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
            applications = dao.recruiment_posts_apply_by_ID(pk)
            # Serialize danh sách các ứng tuyển
            serializer = JobApplicationSerializer(applications, many=True)
            # Trả về danh sách các ứng tuyển dưới dạng JSON
            return Response(serializer.data, status=status.HTTP_200_OK)
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
                return Response({"message": "Recruitment post hidden successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # Viết API xem bài đăng tuyển mới nhất
    # /recruitments_post/newest/
    @action(detail=False, methods=['get'])
    def newest(self, request):
        try:
            # Lấy bài đăng tuyển mới nhất bằng cách sắp xếp theo trường created_date giảm dần và lấy bài đăng đầu tiên
            newest_post = RecruitmentPost.objects.order_by('-created_date').first()
            serializer = self.get_serializer(newest_post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "No recruitment post found."}, status=status.HTTP_404_NOT_FOUND)

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
            # Serialize danh sách các bài đăng tuyển dụng
            serializer = RecruitmentPostSerializer(reported_posts, many=True)
            # Trả về danh sách các bài đăng tuyển dụng dưới dạng JSON
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "No reported recruitment posts found."}, status=status.HTTP_404_NOT_FOUND)

    # API ứng tuyển vào một bài đăng tuyển dụng
    # /recruitments_post/<pk>/apply/
    @action(methods=['post'], detail=True)
    def apply(self, request, pk=None):
        try:
            # Kiểm tra xem bài đăng tuyển dụng tồn tại hay không
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            # Tạo một JobApplication mới
            job_application_data = {
                'recruitment': recruitment_post.id,
                'applicant': request.user.applicant.id,  # user đã được xác định ở middleware
                'is_student': request.data.get('is_student', False),
                # Lấy trường is_student từ request.data, mặc định là False nếu không có
                'date': datetime.now(),  # Sử dụng ngày giờ hiện tại cho trường date
                'status': request.data.get('status', 'Pending'),
                # Lấy trường status từ request.data, mặc định là 'Pending' nếu không có
                'coverLetter': request.data.get('coverLetter'),  # Lấy trường coverLetter từ request.data
            }
            serializer = JobApplicationSerializer(data=job_application_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Trả về thông tin về ứng tuyển mới được tạo dưới dạng JSON response
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

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

    # API đánh giá một bài tuyển dụng
    # /recruitments_post/<pk>/ratings/
    @action(methods=['get', 'post'], detail=True, url_path='ratings', url_name='ratings')
    def create_rating(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            if request.method == 'GET':
                # Lấy danh sách rating của bài đăng
                ratings = recruitment_post.rating_set.all()

                # Phân trang danh sách rating
                paginator = paginators.RatingPaginator()
                paginated_ratings = paginator.paginate_queryset(ratings, request)

                # Serialize danh sách rating
                serializer = RatingSerializer(paginated_ratings, many=True)

                # Trả về danh sách rating đã phân trang
                return paginator.get_paginated_response(serializer.data)

            elif request.method == 'POST':
                # Tạo một đánh giá mới
                user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
                if user:
                    rating_data = {
                        'recruitment_post': recruitment_post.id,
                        'rating': request.data.get('rating'),
                    }
                    if user.__class__.__name__.lower() == 'applicant':
                        rating_data['applicant'] = user.applicant.id
                    elif user.__class__.__name__.lower() == 'employer':
                        rating_data['employer'] = user.employer.id

                    serializer = RatingSerializer(data=rating_data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    # Trả về thông tin về đánh giá mới được tạo
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "User is not an applicant or employer."},
                                    status=status.HTTP_400_BAD_REQUEST)

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
            # Kiểm tra quyền chỉnh sửa Rating: chỉ người tạo mới được chỉnh sửa, admin cũng không được cập nhật
            user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
            if user != rating.applicant and user != rating.employer:
                return Response({"error": "You do not have permission to delete this rating."},
                                status=status.HTTP_403_FORBIDDEN)

            # Cập nhật một phần của rating
            for key, value in request.data.items():
                setattr(rating, key, value)
            rating.save()
            # Serialize và trả về thông tin cập nhật của rating
            serializer = RatingSerializer(rating)
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

            # Kiểm tra quyền xóa rating: chỉ có người tạo và admin mới được xóa
            user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
            if user != rating.applicant and user != rating.employer and not request.user.is_staff:
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            # Xóa rating
            rating.delete()

            return Response({"message": "Rating deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Rating.DoesNotExist:
            return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)



    # API  tạo mới một comment trong bài đăng tuyển dụng + Xem danh sách comment của bài đăng tuyển dụng
    # /recruitments_post/<pk>/comments/
    @action(methods=['get', 'post'], detail=True, name='comments', url_path='comments', url_name='comments')
    def create_comment(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)

            if request.method == 'GET':
                # Lấy danh sách comment của bài đăng
                comments = recruitment_post.comment_set.all()

                # Phân trang danh sách comment
                paginator = paginators.CommentPaginator()
                paginated_comments = paginator.paginate_queryset(comments, request)

                # Serialize danh sách comment
                serializer = CommentSerializer(paginated_comments, many=True)

                # Trả về danh sách comment đã phân trang
                return paginator.get_paginated_response(serializer.data)

            elif request.method == 'POST':
                # Tạo một comment mới
                user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
                if user:
                    comment_data = {
                        'recruitment': recruitment_post.id,
                        'content': request.data.get('content'),
                        user.__class__.__name__.lower(): user.id,
                    }
                    serializer = CommentSerializer(data=comment_data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    # Trả về thông tin về comment mới được tạo
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "User is not an applicant or employer."},
                                    status=status.HTTP_400_BAD_REQUEST)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API reply commment trong một bài tuyển dụng nhất định
    # /recruitments_post/<pk>/comments/<comment_pk>/reply_comment/
    @action(detail=True, methods=['get', 'post'], url_path='comments/(?P<comment_pk>\d+)/reply_comment',
            url_name='reply_comment')
    def reply_comment(self, request, pk=None, comment_pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)
            # Lấy comment cha từ comment_pk
            parent_comment = get_object_or_404(Comment, pk=comment_pk)

            if request.method == 'GET':
                # Lấy danh sách các reply comment cho comment cha
                replies = parent_comment.replies.all()
                # Phân trang danh sách reply comment
                paginator = paginators.CommentReplyPaginator()
                paginated_replies = paginator.paginate_queryset(replies, request)
                # Serialize danh sách reply comment
                serializer = CommentSerializer(paginated_replies, many=True)
                # Trả về danh sách comment đã phân trang
                return paginator.get_paginated_response(serializer.data)

            elif request.method == 'POST':
                user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
                if user:
                    reply_comment = Comment.objects.create(
                        recruitment=recruitment_post,
                        content=request.data.get('content'),
                        parent=parent_comment,
                        **{user.__class__.__name__.lower(): user}  # UNPACK để tạo keyword
                    )
                    serializer = CommentSerializer(reply_comment)
                    # Trả về thông tin về reply comment mới được tạo
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "User is not an applicant or employer."},
                                    status=status.HTTP_400_BAD_REQUEST)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

    # API xóa comment trong bài đăng tuyển dụng => Xóa luôn các comment là con
    # /recruitments_post/<pk>/comments/<comment_id>/delete/
    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>\\d+)/delete', url_name='delete_comment')
    def delete_comment(self, request, pk=None, comment_id=None):
        try:
            recruitment_post = get_object_or_404(RecruitmentPost, pk=pk)
            comment = get_object_or_404(Comment, pk=comment_id)

            if comment.recruitment != recruitment_post:
                return Response({"error": "Comment does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
            if user != comment.applicant and user != comment.employer and not request.user.is_staff:
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

            user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
            if user != reply.applicant and user != reply.employer and not request.user.is_staff:
                return Response({"error": "You do not have permission to delete this reply."},
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

            user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
            if user != comment.applicant and user != comment.employer:
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            # Cập nhật một phần của comment
            for key, value in request.data.items():
                setattr(comment, key, value)
            comment.save()

            return Response(CommentSerializer(comment).data, status=status.HTTP_200_OK)

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

            user = getattr(request.user, 'applicant', None) or getattr(request.user, 'employer', None)
            if user != reply.applicant and user != reply.employer:
                return Response({"error": "You do not have permission to update this reply."},
                                status=status.HTTP_403_FORBIDDEN)

            for key, value in request.data.items():
                setattr(reply, key, value)
            reply.save()

            return Response({"message": "Reply updated successfully."}, status=status.HTTP_200_OK)

        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({"error": "Comment or reply not found."}, status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserSerializer
    serializer_class = serializers.UserSerializer
    # Dùng upload ảnh lên Cloud
    parser_classes = [parsers.MultiPartParser, ]

    # API xem chi tiết tài khoản hiện (chỉ xem được của mình) + cập nhật tài khoản (của mình)
    # /users/current-user/
    @action(methods=['get', 'patch'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        # Đã được chứng thực rồi thì không cần truy vấn nữa => Xác định đây là người dùng luôn
        # user = user hiện đang đăng nhập
        user = request.user
        # Khi so sánh thì viết hoa hết
        if request.method.__eq__('PATCH'):

            for k, v in request.data.items():
                # Thay vì viết user.first_name = v
                setattr(user, k, v)
            user.save()

        return Response(serializers.UserSerializer(user).data)

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





class EmployerViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Employer.objects.all()
    serializer_class = serializers.EmployerSerializer


class ApplicantViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Applicant.objects.all()
    serializer_class = serializers.ApplicantSerializer
    # Thiết lập lớp phân trang (pagination class) cho một API view cụ thể.
    pagination_class = paginators.ApplicantPagination
    def get_queryset(self):
        skills = self.request.query_params.getlist('skills')
        areas = self.request.query_params.getlist('areas')
        careers = self.request.query_params.getlist('careers')
        position = self.request.query_params.get('position')

        queryset = Applicant.objects.all()

        if skills:
            queryset = queryset.filter(skills__name__in=skills).distinct()

        if areas:
            queryset = queryset.filter(areas__name__in=areas).distinct()

        if careers:
            queryset = queryset.filter(career__name__in=careers)
        if position:
            queryset = queryset.filter(position__icontains=position)
        return queryset
