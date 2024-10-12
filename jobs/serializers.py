from rest_framework import serializers
from jobs.models import (User, Applicant, Skill, Area, Career, EmploymentType, Employer, Status, RecruitmentPost,
                         JobApplication, Notification, Review, PasswordResetToken, Message)
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import COMPANY_CHOICES
User = get_user_model()

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id','name']


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id','name']


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = ['id','name']

class EmploymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentType
        fields = ['id', 'type']


class StatusSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'role']


# Dùng để tạo User
class UserSerializer(serializers.ModelSerializer):
    # CHỈ ĐƯỜNG DẪN TUYỆT ĐỐI ẢNH ĐƯỢC UP TRÊN CLOUDINARY
    # to_representation ùy chỉnh cách biểu diễn (representation) của một đối tượng (instance) khi nó được chuyển đổi thành dữ liệu JSON
    # hoặc dữ liệu khác để trả về cho client.
    # instance ở đây là User
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.avatar:
            req['avatar'] = instance.avatar.url
        return req

    class Meta:
        model = User
        # Qua models.py -> ctrl + trỏ vào AbstractUser để thấy được các trường củ User
        fields = ['id','first_name', 'last_name', 'username', 'password', 'gender', 'email', 'mobile', 'avatar', ]

        # Thiết lập mật khẩu chỉ để ghi
        extra_kwargs = {
            'password': {
                'write_only': True
            }

        }
    # Băm mật khẩu
    def create(self, validated_data):
        data = validated_data.copy()
        user = User(**data)
        user.set_password(data['password'])
        user.save()
        return user

    # def update(self, validated_data):
    #     data = validated_data.copy()
    #     user = User(**data)
    #     user.set_password(data['password'])
    #     user.save()
    #     return user


# Hỗ trợ cho phần view application
class ViewUserSerializer(serializers.ModelSerializer):
    # CHỈ ĐƯỜNG DẪN TUYỆT ĐỐI ẢNH ĐƯỢC UP TRÊN CLOUDINARY
    # to_representation ùy chỉnh cách biểu diễn (representation) của một đối tượng (instance) khi nó được chuyển đổi thành dữ liệu JSON
    # hoặc dữ liệu khác để trả về cho client.
    # instance ở đây là User
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.avatar:
            req['avatar'] = instance.avatar.url
        return req

    class Meta:
        model = User
        # Qua models.py -> ctrl + trỏ vào AbstractUser để thấy được các trường củ User
        fields = ['id','first_name', 'last_name', 'gender', 'email', 'mobile', 'avatar', ]


# Phần tạo ApplicantCreateSerializer trong user....
class ApplicantCreateSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(many=True, queryset=Skill.objects.all(), required=False)
    areas = serializers.PrimaryKeyRelatedField(many=True, queryset=Area.objects.all(), required=False)
    career = serializers.PrimaryKeyRelatedField(queryset=Career.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Applicant
        fields = ['position', 'salary_expectation', 'experience', 'cv', 'skills', 'areas', 'career']

    def create(self, validated_data):
        skills_data = validated_data.pop('skills', [])
        areas_data = validated_data.pop('areas', [])
        career_data = validated_data.pop('career', None)

        applicant = Applicant.objects.create(**validated_data)

        if skills_data:
            applicant.skills.set(skills_data)

        if areas_data:
            applicant.areas.set(areas_data)

        if career_data:
            applicant.career = career_data

        applicant.save()
        return applicant

    # class Meta:
    #     model = Applicant
    #     fields = ['position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']
    # Thêm đường dẫn cho ảnh của CV
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req


# Phần để cập nhật put patch applicant
class ApplicantUpdateSerializer(serializers.ModelSerializer):
    career = serializers.PrimaryKeyRelatedField(queryset=Career.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Applicant
        fields = ['position', 'salary_expectation', 'experience', 'cv', 'career', 'areas']
        extra_kwargs = {
            'areas': {
                'read_only': True
            }
        }
    def create(self, validated_data):
        career_data = validated_data.pop('career', None)

        applicant = Applicant.objects.create(**validated_data)

        if career_data:
            applicant.career = career_data

        applicant.save()
        return applicant

    # class Meta:
    #     model = Applicant
    #     fields = ['position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']
    # Thêm đường dẫn cho ảnh của CV
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req

# Dùng để hiển thị ApplicantSerializer
class ApplicantSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()
    career = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    def get_skills(self, obj):
        skills = obj.skills.all()
        return SkillSerializer(skills, many=True).data

    def get_areas(self, obj):
        areas = obj.areas.all()
        return AreaSerializer(areas, many=True).data
    def get_career(self, obj):
        try:
            career = obj.career
            return CareerSerializer(career).data
        except Career.DoesNotExist:
            return None
    def get_user(self, obj):
        try:
            user = obj.user
            return ViewUserSerializer(user).data
        except User.DoesNotExist:
            return None
    class Meta:
        model = Applicant
        fields = ['id', 'user', 'position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']
    # Thêm đường dẫn cho ảnh của CV
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req

# Nằm trong phần hiển thị view application
class ViewApplicantSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()
    career = serializers.SerializerMethodField()
    user = ViewUserSerializer()
    def get_skills(self, obj):
        skills = obj.skills.all()
        return SkillSerializer(skills, many=True).data

    def get_areas(self, obj):
        areas = obj.areas.all()
        return AreaSerializer(areas, many=True).data
    def get_career(self, obj):
        try:
            career = obj.career
            return CareerSerializer(career).data
        except Career.DoesNotExist:
            return None
    def get_user(self, obj):
        try:
            user = obj.user
            return ViewUserSerializer(user).data
        except User.DoesNotExist:
            return None

    class Meta:
        model = Applicant
        fields = ['id','user', 'position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']
    # Thêm đường dẫn cho ảnh của CV
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req

class CreatePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentPost
        fields = ['title', 'description', 'company', 'location', 'salary', 'active']

# Phần để hiển thị trong comment
class ApplicantCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Applicant
        fields = ['user', 'position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']

# Phần để hiển thị trong comment
class EmployerCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Employer
        fields = ['user', 'companyName', 'position', 'information', 'address', 'company_website', 'company_type', 'company_type_display']

# Phần để hiển thị
class EmployerSerializer(serializers.ModelSerializer):
    company_type_display = serializers.SerializerMethodField()
    class Meta:
        model = Employer
        fields = ['id', 'companyName', 'position', 'information', 'address', 'company_website', 'company_type', 'company_type_display']
    def get_company_type_display(self, obj):
        return dict(COMPANY_CHOICES).get(obj.company_type)


# Phần để tạo
class EmployerCreateSerializer(serializers.ModelSerializer):
    company_type_display = serializers.SerializerMethodField()
    class Meta:
        model = Employer
        fields = ['id', 'companyName', 'position', 'information', 'address', 'company_website', 'company_type', 'company_type_display']
    def get_company_type_display(self, obj):
        return dict(COMPANY_CHOICES).get(obj.company_type)




# Phần để hiển thị
class UserDetailSerializer(serializers.ModelSerializer):
    # Serializer cho thông tin của Applicant
    applicant = serializers.SerializerMethodField()
    # Serializer cho thông tin của Employer
    employer = serializers.SerializerMethodField()
    # Phương thức để lấy thông tin của Applicant
    def get_applicant(self, obj):
        try:
            applicant = obj.applicant
            return ApplicantSerializer(applicant).data
        except Applicant.DoesNotExist:
            return None
    # Phương thức để lấy thông tin của Employer
    def get_employer(self, obj):
        try:
            employer = obj.employer
            return EmployerSerializer(employer).data
        except Employer.DoesNotExist:
            return None

    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'username', 'email', 'mobile', 'avatar', 'is_employer', 'applicant', 'employer','is_staff','is_superuser']
        # depth = 1

    # CHỈ ĐƯỜNG DẪN TUYỆT ĐỐI ẢNH ĐƯỢC UP TRÊN CLOUDINARY
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.avatar:
            req['avatar'] = instance.avatar.url
        return req

# Cập nhật một phần nào đó của user(username và mật khẩu là bắt buộc)
class PatchUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'email', 'mobile', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'username': {'required': False},
            'email': {'required': False},
            'mobile': {'required': False},
            'avatar': {'required': False},
        }

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance



class RecruitmentPostSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer()
    career = CareerSerializer()
    employmenttype = EmploymentTypeSerializer()
    area = AreaSerializer()
    # Tạo đường dẫn tuyệt đối cho trường image (image upload lên Cloudinary)
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.image:
            req['image'] = instance.image.url
        return req
    class Meta:
        model = RecruitmentPost
        fields = [
            'id', 'employer', 'image', 'career', 'employmenttype', 'area',
            'title', 'deadline', 'quantity', 'gender', 'location', 'salary',
            'position', 'description', 'experience', 'reported', 'created_date',
            'updated_date', 'active'
        ]

class HideRecruitmentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentPost
        fields = [
            'id', 'employer', 'image', 'career', 'employmenttype', 'area',
            'title', 'deadline', 'quantity', 'gender', 'location', 'salary',
            'position', 'description', 'experience', 'reported', 'created_date',
            'updated_date', 'active'
        ]
        read_only_fields = [
            'id', 'employer', 'image', 'career', 'employmenttype', 'area',
            'title', 'deadline', 'quantity', 'gender', 'location', 'salary',
            'position', 'description', 'experience', 'reported', 'created_date',
            'updated_date'
        ]


# Phần để tạo
class CreateRecruitmentPostSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.image:
            req['image'] = instance.image.url
        return req
    class Meta:
        model = RecruitmentPost
        fields = '__all__'
        extra_kwargs = {
            'employmenttype': {'required': False, 'allow_null': True},
            # 'area': {'required': False, 'allow_null': True},
            # 'deadline': {'required': False, 'allow_null': True},
            # 'quantity': {'required': False, 'allow_null': True},
            'location': {'required': False, 'allow_null': True},
            # 'salary': {'required': False, 'allow_null': True},
            'position': {'required': False, 'allow_null': True},
            'experience': {'required': False, 'allow_null': True},
        }



# # Phần hiển thị comment
# class CommentSerializer(serializers.ModelSerializer):
#     recruitmentPost = serializers.SerializerMethodField()
#     def get_recruitmentPost(self, obj):
#         return RecruitmentPostSerializer(obj.recruitmentPost).data
#
#     class Meta:
#         model = Comment
#         fields = '__all__'
#         # depth = 1


# Phần hiển thị Review
class ReviewSerializer(serializers.ModelSerializer):
    recruitmentPost = serializers.SerializerMethodField()
    def get_recruitmentPost(self, obj):
        return RecruitmentPostSerializer(obj.recruitmentPost).data

    class Meta:
        model = Review
        fields = '__all__'
        # depth = 1

# Phần cho Post để comment
class RecruitmentPostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentPost
        fields = ['id', 'title', 'image']


# Phần tạo Review
class CreateReviewSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5, default=5)

    class Meta:
        model = Review
        fields = ['id', 'recruitment', 'user', 'rating', 'content']

    def validate(self, data):
        # Đảm bảo rằng thông tin người dùng được cung cấp trong ngữ cảnh của request
        if 'user' not in self.context:
            raise serializers.ValidationError("User information required.")
        return data

# Phần xem Review
class ReviewSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer()
    class Meta:
        model = Review
        fields = ['id', 'recruitment', 'user', 'rating', 'content', 'created_date', 'updated_date']

class JobApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'status']



# Phần hiển thị view application và list view applications
class JobApplicationSerializer(serializers.ModelSerializer):
    applicant = ViewApplicantSerializer()
    recruitment = RecruitmentPostCommentSerializer()
    status = StatusSerialzier()
    class Meta:
        model = JobApplication
        fields = ['id', 'is_student', 'applicant', 'coverLetter', 'status', 'recruitment']
        extra_kwargs = {
            'status': {
                'read_only': True
            }
        }

    # def create(self, validated_data):
    #     validated_data['status'] = Status.objects.get(role='Pending')
    #     return super().create(validated_data)

# class JobApplicationStatusSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = JobApplication
#         fields = ['id', 'recruitment', 'applicant', 'status', 'coverLetter', 'is_student']

# class IdPost(serializers.ModelSerializer):
#     class Meta:
#         model = RecruitmentPost
#         fields = ['id']
# class IdApplicant(serializers.ModelSerializer):
#     class Meta:
#         model = Applicant
#         fields = ['id']


# Cái để tạo
class CreateJobApplicationStatusSerializer(serializers.ModelSerializer):
    # applicant = IdApplicant()
    # recruitment = IdPost()
    class Meta:
        model = JobApplication
        fields = [ 'id','coverLetter', 'is_student', 'applicant', 'recruitment']



class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Notification
        fields = '__all__'


# Xử lý phần Like -> Đăng nhập thì like nó đổi màu (phần RecruitmentPost)
# AuthenticatedRecruitmentPostSerializer : xử lý phần tô đậm khi like (đăng nhập rồi khi like thì sẽ tô đậm)
class AuthenticatedRecruitmentPostSerializer(RecruitmentPostSerializer):
    liked = serializers.SerializerMethodField()

    # lesson chính là instance ở phía dưới class Meta
    def get_liked(self, RecruitmentPost):
        # exists : có tồn tại không
        return RecruitmentPost.like_set.filter(active=True).exists()

    class Meta:
        model = RecruitmentPost
        fields = RecruitmentPostSerializer.Meta.fields + ['liked']






class PasswordResetSerializer(serializers.ModelSerializer):
    token = serializers.IntegerField()
    new_password = serializers.CharField(write_only=True, min_length=1,)


    def validate_token(self, value):
        """
        Kiểm tra xem mã xác thực có tồn tại và hợp lệ không.
        """
        try:
            token = PasswordResetToken.objects.get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid verification code.")

        if token.is_expired():
            raise serializers.ValidationError("The verification code has expired.")

        self.context['token'] = token
        return value

    def validate_new_password(self, value):
        """
        Xác thực mật khẩu mới.
        """
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters.")
        return value

    def save(self):
        """
        Thay đổi mật khẩu cho người dùng nếu mã xác thực hợp lệ.
        """
        token = self.context['token']
        user = token.user
        user.set_password(self.validated_data['new_password'])  # set_password(): tự động băm mật khẩu
        user.save()
        # Xóa mã xác thực sau khi sử dụng
        token.delete()
        return user

    class Meta:
        model =  User
        fields = ['token', 'new_password']



class EmailSerializer(serializers.Serializer):
    """
    Reset Password Email Request Serializer.
    """

    email = serializers.EmailField()

    class Meta:
        fields = ("email",)

# Kiểm tra sự tồn tại của email
class EmailCheckSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    class Meta:
        fields = ("email",)


# Kiểm tra sự tồn tại của token
class TokenCheckSerializer(serializers.Serializer):
    token = serializers.IntegerField()
    class Meta:
        fields = ("token",)

    def validate_token(self, value):
        if not PasswordResetToken.objects.filter(token=value).exists():
            raise serializers.ValidationError("Token not found.")
        return value

# Kiểm tra sự tồn tại của review
class ReviewStatusSerializer(serializers.Serializer):
    hasReviewed = serializers.BooleanField()
    class Meta:
        fields = ("hasReviewed",)


# class MessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Message
#         fields = ['id', 'sender', 'text', 'created_at']
#
# class ChatSerializer(serializers.ModelSerializer):
#     messages = MessageSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Chat
#         fields = ['id', 'applicant', 'employer', 'messages', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'sender_username', 'text', 'created_at']

# RegistereEmployerSerializer
class RegistereEmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'id']