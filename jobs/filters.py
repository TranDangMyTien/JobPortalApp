import django_filters
from .models import RecruitmentPost

class RecruitmentPostFilter(django_filters.FilterSet):
    min_salary = django_filters.NumberFilter(field_name='salary', lookup_expr='gte')
    max_salary = django_filters.NumberFilter(field_name='salary', lookup_expr='lte')

    class Meta:
        model = RecruitmentPost
        fields = ['min_salary', 'max_salary']






