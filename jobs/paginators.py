from rest_framework.pagination import PageNumberPagination

class RecruitmentPostPaginator(PageNumberPagination):
    page_size = 20  # Mỗi trang sẽ chứa tối đa 20 bài đăng tuyển dụng.

# Phân trang cho Comment
class CommentPaginator(PageNumberPagination):
    page_size = 10  # Số lượng comment hiển thị trên mỗi trang
    max_page_size = 20  # Số lượng comment tối đa trên mỗi trang

# Phân trang reply comment
class CommentReplyPaginator(PageNumberPagination):
    page_size = 10  # Số lượng reply comment hiển thị trên mỗi trang
    max_page_size = 20  # Số lượng reply comment tối đa trên mỗi trang

# Phân trang cho Rating
class RatingPaginator(PageNumberPagination):
    page_size = 10  # Số lượng rating hiển thị trên mỗi trang
    max_page_size = 20  # Số lượng rating tối đa trên mỗi trang