from rest_framework import serializers
from jobs.models import (User, Applicant, Skill, Area, Career, EmploymentType, Employer, Status, RecruitmentPost,
                         Rating, Comment, JobApplication, Notification)
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

# Dùng để hiển thị ApplicantSerializer
class ApplicantSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()
    career = serializers.SerializerMethodField()
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
    class Meta:
        model = Applicant
        fields = ['position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']
    # Thêm đường dẫn cho ảnh của CV
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req

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
        fields = ['id','first_name', 'last_name', 'username', 'email', 'mobile', 'avatar', 'applicant', 'employer']
        depth = 1




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
        fields = '__all__'



class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    # Một comment cho 1 người tạo nên không gán many = True
    # employer = EmployerSerializer()
    # applicant = ApplicantSerializer()
    employer = serializers.SerializerMethodField()
    applicant = serializers.SerializerMethodField()

    def get_employer(self, obj):
        return EmployerSerializer(obj.employer).data

    def get_applicant(self, obj):
        return ApplicantSerializer(obj.applicant).data

    class Meta:
        model = Comment
        fields = '__all__'
        depth = 1


class JobApplicationSerializer(serializers.ModelSerializer):
    applicant = ApplicantSerializer()
    status = StatusSerialzier()
    recruitment = RecruitmentPostSerializer()
    class Meta:
        model = JobApplication
        fields = ['is_student', 'recruitment', 'applicant', 'coverLetter', ]
        read_only_fields = ['status']
        depth = 1

    def create(self, validated_data):
        validated_data['status'] = Status.objects.get(role='Pending')
        return super().create(validated_data)

class JobApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'recruitment', 'applicant', 'status', 'coverLetter', 'is_student']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Notification
        fields = '__all__'


