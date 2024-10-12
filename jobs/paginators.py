from rest_framework.pagination import PageNumberPagination

class RecruitmentPostPaginator(PageNumberPagination):
    page_size = 10  # Mỗi trang sẽ chứa tối đa 10 bài đăng tuyển dụng.
    max_page_size = 20

# Phân trang cho Comment
class CommentPaginator(PageNumberPagination):
    page_size = 10
    max_page_size = 20

# Phân trang reply comment
class CommentReplyPaginator(PageNumberPagination):
    page_size = 10  # Số lượng reply comment hiển thị trên mỗi trang
    max_page_size = 20

# Phân trang cho Rating
class ReviewPaginator(PageNumberPagination):
    page_size = 10  # Số lượng rating hiển thị trên mỗi trang
    max_page_size = 20

# Phân trang cho Applicant
class ApplicantPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20

# Phân trang cho User
class UserPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20

# Phân trang cho Application
class ApplicationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20