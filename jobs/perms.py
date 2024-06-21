from rest_framework import permissions


# Là Admin và xác thực
class AdminIsAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return bool(request.user.is_staff or request.user.is_superuser and request.user.is_authenticated)

# Là admin hoặc là người tự tạo ra obj
class IsAdminOrSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or request.user == obj)

# Người dùng xác thực và là chủ sở hữu (applicant)
class AppOwnerAuthenticated(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        # Kiểm tra xem người dùng có quyền chung hay không (IsAuthenticated)
        is_authenticated = self.has_permission(request, view)

        # Kiểm tra xem người dùng có phải là chủ sở hữu của đối tượng hay không
        is_owner = request.user.applicant == obj

        # Chỉ cho phép truy cập nếu cả hai điều kiện đều đúng
        return is_authenticated and is_owner

# Người dùng xác thực và là chủ sở hữu (employer)
class EmOwnerAuthenticated(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        # Kiểm tra xem người dùng có được xác thực không
        is_authenticated = self.has_permission(request, view)

        # Kiểm tra xem người dùng có phải là chủ sở hữu của đối tượng hay không
        is_owner = request.user.employer == obj

        # Trả về True nếu cả hai điều kiện đều đúng
        return is_authenticated and is_owner

# Viết tắt
# class EmOwnerAuthenticated(permissions.IsAuthenticated):
#     def has_object_permission(self, request, view, obj):
#         return self.has_permission(request, view) and request.user.employer == obj

# Là Employer và xác thực
class EmIsAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        # Check if the user is authenticated first
        if not request.user.is_authenticated:
            return False

        # Now check if the authenticated user has the 'employer' attribute
        return hasattr(request.user, 'employer')

# Là Application và xác thực
class AppIsAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        # Check if the user is authenticated first
        if not request.user.is_authenticated:
            return False

        # Now check if the authenticated user has the 'applicant' attribute
        return hasattr(request.user, 'applicant')

# Kết hợp cả hai lớp phân quyền
class IsAdminOrSelfOrEmIsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return IsAdminOrSelf().has_permission(request, view) or EmIsAuthenticated().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return IsAdminOrSelf().has_object_permission(request, view, obj) or EmIsAuthenticated().has_permission(request, view)

# permissions.IsAuthenticated kiểm tra xem người dùng có được xác thực hay không.

# has_object_permission Kiểm tra quyền truy cập đối với một đối tượng cụ thể + Kiểm tra chủ sở hữu (obj)
# => Kiểm tra quyền truy cập vào một đối tượng cụ thể, đảm bảo người dùng là chủ sở hữu của đối tượng đó.

# has_permission Kiểm tra quyền truy cập vào một view cụ thể

