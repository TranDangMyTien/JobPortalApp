from django.shortcuts import render
from jobs.models import RecruitmentPost
from jobs import serializers
from jobs import paginators
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import viewsets, generics, permissions, status, parsers
from rest_framework.decorators import action
from django.db.models import Count
from jobs import dao
from .models import JobApplication, Employer, Applicant, User
from .serializers import JobApplicationSerializer, RatingSerializer, CommentSerializer
from django.shortcuts import get_object_or_404
from datetime import datetime

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

    queryset = RecruitmentPost.objects.filter(active=True).order_by('id')
    # Trong Django REST Framework, khi bạn thiết lập một API view, bạn cần xác định loại dữ liệu nào sẽ được sử dụng để biểu diễn dữ liệu trả về từ API đó.
    # Điều này được thực hiện thông qua việc chỉ định một lớp serializer bằng cách sử dụng thuộc tính serializer_class.
    # Đoạn mã này đang chỉ định rằng API view sẽ sử dụng lớp serializer RecruitmentPostSerializer từ module serializers
    # Nói cách khác, khi bạn truy vấn dữ liệu từ model RecruitmentPost, dữ liệu sẽ được trả về dưới dạng các đối tượng RecruitmentPost, và sau đó được chuyển đổi thành định dạng JSON
    # (hoặc XML) thông qua serializer này trước khi được trả về từ API.
    serializer_class = serializers.RecruitmentPostSerializer  # Tùy chỉnh cách dữ liệu được biểu diễn và xử lý trước khi nó được gửi đến client

    # Thiết lập lớp phân trang (pagination class) cho một API view cụ thể.
    pagination_class = paginators.RecruitmentPostPaginator

    # PHẦN LỌC DỮ LIỆU
    def get_queryset(self):
        # queries = self.queryset: Gán self.queryset cho biến queries. self.queryset
        # chứa tất cả các bài đăng tuyển dụng có trạng thái active=True.
        queries = self.queryset

        # LỌC CÁC BÀI ĐĂNG TUYỂN HẾT THỜI HẠN
        # Vòng lặp for q in queries: Duyệt qua mỗi đối tượng RecruitmentPost trong queries
        for q in queries:
            #  Kiểm tra xem ngày hết hạn của RecruitmentPost (q.deadline) có nhỏ hơn hoặc bằng ngày hiện tại không.
            # Điều này đảm bảo rằng chỉ có các bài đăng tuyển dụng đã hết hạn sẽ bị vô hiệu hóa.
            if q.deadline <= timezone.now().date():
                #  Đặt thuộc tính active của bài đăng tuyển dụng (RecruitmentPost) thành False,
                #  ngăn chặn nó khỏi hiển thị trong các kết quả tìm kiếm hoặc các yêu cầu khác.
                q.active = False
                # Lưu thay đổi vào cơ sở dữ liệu.
                q.save()

        # PHẦN KIỀM KIẾM
        if self.action.__eq__('list'):
            title = self.request.query_params.get('title')
            # Nếu q khác null có nghĩa là truy vấn
            if title:
                # recruitments_post/?tile=
                queries = queries.filter(title__icontains=title)

            employer = self.request.query_params.get('employer_id')
            if employer:
                # Dùng employer__id: thì nó join 2 bảng lại với nhau
                # Ví dụ tìm 10 lần tìm thì nó join lại 10 lần => Tốn chi phí và thời gian
                # Nên dùng employer_id vì nó được chương trình sinh ra sẵn cho khóa ngoại của mỗi bảng
                # Ở class RecruitmentPost có trường khóa ngoại employer => Django sinh ra 1 trường mới là employer_id
                # /recruitments_post/?employer_id=
                queries = queries.filter(employer_id=employer)

            career = self.request.query_params.get('career')
            if career:
                # /recruitments_post/?career=
                queries = queries.filter(career__name__icontains=career)

            employment_type = self.request.query_params.get('employment_type')
            if employment_type:
                # /recruitments_post/?employment_type=
                queries = queries.filter(employmenttype__type__icontains=employment_type)

            location = self.request.query_params.get('location')
            if location:
                # /recruitments_post/?location=
                queries = queries.filter(location__icontains=location)
        # Trả về queries sau khi đã thực hiện các thay đổi
        return queries

    # API xem danh sách bài đăng tuyển dụng phổ biến (được apply nhiều) (giảm dần theo số lượng apply)
    # /recruitments_post/popular/
    @action(detail=False, methods=['get'])
    def popular(self, request):
        try:
            # Lấy danh sách các bài đăng tuyển dụng được sắp xếp theo số lượng apply giảm dần
            # Truy vấn ngược
            recruitment_posts = dao.recruiment_posts_by_appy()
            serializer = serializers.RecruitmentPostSerializer(recruitment_posts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment posts not found."}, status=status.HTTP_404_NOT_FOUND)

    # API Đếm số lượng apply của 1 bài đăng theo id
    # /recruitments_post/pk=?/num_applications
    @action(detail=True, methods=['get'])
    def num_applications(self, request, pk=None):
        try:
            num_applications = dao.count_apply_by_id_recruiment_post(pk)
            # Trả về số lượng đơn ứng tuyển dưới dạng JSON
            return Response({"num_applications": num_applications}, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)


    # API lấy danh sách các apply của 1 bài đăng (theo id)
    # /recruitments_post/pk=?/list_apply/
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

    # API để xem các đánh giá của một bài đăng tuyển dựa trên id bài đăng (do người dùng nhập)
    # /recruitments_post/pk=?/rating/
    @action(detail=True, methods=['get'])
    def rating(self, request, pk=None):
        try:
            ratings = dao.recruiment_posts_list_rating_by_ID(pk)
            # Serialize danh sách các đánh giá
            serializer = RatingSerializer(ratings, many=True)
            # Trả về danh sách các đánh giá dưới dạng JSON
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            # Trả về thông báo lỗi nếu không tìm thấy bài đăng tuyển dụng
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # API để xem các bình luận của một bài đăng tuyển dựa trên id bài đăng (do người dùng nhập)
    # /recruitments_post/pk=?/rating/
    @action(detail=True, methods=['get'])
    def comment(self, request, pk=None):
        try:
            comments = dao.recruiment_posts_list_comment_by_ID(pk)
            # Serialize danh sách các đánh giá
            serializer = CommentSerializer(comments, many=True)
            # Trả về danh sách các đánh giá dưới dạng JSON
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RecruitmentPost.DoesNotExist:
            # Trả về thông báo lỗi nếu không tìm thấy bài đăng tuyển dụng
            return Response({"error": "Recruitment post not found."}, status=status.HTTP_404_NOT_FOUND)

    # Viết API đếm xem mỗi bài đăng có bao nhiêu lượt like, dựa trên ID bài đăng (do người dùng nhập)
    # /recruitments_post/pk=?/count_likes/
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
    # /recruitments_post/pk=?/hide_post/
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
    # /recruitments_post/pk=?/report/
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



class UserViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserSerializer


class EmployerViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Employer.objects.all()
    serializer_class = serializers.EmployerSerializer


class ApplicantViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Applicant.objects.all()
    serializer_class = serializers.ApplicantSerializer

