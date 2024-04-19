from rest_framework.pagination import PageNumberPagination

class RecruitmentPostPaginator(PageNumberPagination):
    page_size = 20  # Mỗi trang sẽ chứa tối đa 20 bài đăng tuyển dụng.
