from rest_framework import serializers
from jobs.models import (User, Applicant, Skill, Area, Career, EmploymentType, Employer, Status, RecruitmentPost,
                         Rating, Comment, JobApplication, Notification)
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

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
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'gender', 'email', 'is_employer',
                  'is_applicant',
                  'is_superuser', 'mobile', 'avatar', ]

        # Thiết lập mật khẩu chỉ để ghi
        extra_kwargs = {
            'password': {
                'write_only': True
            }

        }


class SkillSerilizer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class AreaSerilizer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = '__all__'


class ApplicantSerializer(serializers.ModelSerializer):
    # user = UserSerializer()
    # skills = SkillSerilizer(many=True)
    # areas = AreaSerilizer(many=True)
    # career = CareerSerializer()

    class Meta:
        model = Applicant
        fields = ['id', 'user', 'position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']





class EmployerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Employer
        fields = ['id', 'user', 'companyName', 'position', 'information', 'address', 'company_website', 'company_type']


class EmploymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentType
        fields = '__all__'



class StatusSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'

class RecruitmentPostSerializer(serializers.ModelSerializer):
    # employer = EmployerSerializer()
    # career = CareerSerializer()
    # employmenttype = EmploymentTypeSerializer()
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
    employer = EmployerSerializer()
    applicant = ApplicantSerializer()

    class Meta:
        model = Comment
        fields = '__all__'



class JobApplicationSerializer(serializers.ModelSerializer):
    # applicant = ApplicantSerializer()
    # status = StatusSerialzier()
    # recruitment = RecruitmentPostSerializer()
    class Meta:
        model = JobApplication
        fields = ['is_student', 'recruitment', 'applicant', 'coverLetter', ]
        read_only_fields = ['status']

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


