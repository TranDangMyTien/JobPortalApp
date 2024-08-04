from rest_framework import serializers
from jobs.models import (User, Applicant, Skill, Area, Career, EmploymentType, Employer, Status, RecruitmentPost,
                         JobApplication, Notification, Review)
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
        fields = ['id','user', 'position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']
    # Thêm đường dẫn cho ảnh của CV
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req



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
        fields = ['id','first_name', 'last_name', 'username', 'password','email', 'mobile', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    # Băm mật khẩu
    def update(self, instance, validated_data):
        # Lấy mật khẩu từ validated_data nếu có
        password = validated_data.pop('password', None)

        # Cập nhật các trường khác cho instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Nếu có mật khẩu mới, băm mật khẩu và cập nhật
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
        fields = ['id', 'title']


# Phần tạo Post để review
class RecruitmentPostReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentPost
        fields = ['id', 'title']


# class CreatRatingSerializer(serializers.ModelSerializer):
#     user = UserDetailSerializer()
#     recruitment = RecruitmentPostCommentSerializer()
#     class Meta:
#         model = Rating
#         fields = ['id', 'recruitment' ,'user', 'rating']


# Tạo comment
# class CreateCommentSerializer(serializers.ModelSerializer):
#     # user = serializers.SerializerMethodField()
#     # user = UserDetailSerializer()
#     # recruitment = serializers.SerializerMethodField()
#     # recruitment = RecruitmentPostCommentSerializer()
#     # def get_user(self, obj):
#     #     return UserDetailSerializer(obj.user).data
#     # def get_recruitment(self, obj):
#     #     return RecruitmentPostSerializer(obj.recruitmentPost).data
#     class Meta:
#         model = Comment
#         fields = ['id','user','content','recruitment', 'created_date']

# Tạo comment
# class ReadCommentSerializer(serializers.ModelSerializer):
#     # user = serializers.SerializerMethodField()
#     # user = UserDetailSerializer()
#     # recruitment = serializers.SerializerMethodField()
#     # recruitment = RecruitmentPostCommentSerializer()
#     # def get_user(self, obj):
#     #     return UserDetailSerializer(obj.user).data
#     # def get_recruitment(self, obj):
#     #     return RecruitmentPostSerializer(obj.recruitmentPost).data
#     class Meta:
#         model = Comment
#         fields = ['id','user','content','recruitment', 'created_date', 'updated_date']

# class CommentParentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Comment
#         fields = ['id','content']

# Tạo comment reply
# class CreateCommentReplySerializer(serializers.ModelSerializer):
#     user = PatchUserSerializer()
#     recruitment = RecruitmentPostCommentSerializer()
#     parent = CommentParentSerializer()
#     class Meta:
#         model = Comment
#         fields = ['parent','user','content','recruitment']



# Phần hiển thị view application và list view applications
class JobApplicationSerializer(serializers.ModelSerializer):
    applicant = ViewApplicantSerializer()
    # status = StatusSerialzier()
    class Meta:
        model = JobApplication
        fields = ['id','is_student','applicant', 'coverLetter','status' ]
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


