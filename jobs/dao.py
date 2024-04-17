from jobs.models import JobApplication
from django.db.models import Count
from datetime import datetime
from django.db.models.functions import ExtractQuarter, ExtractYear


def count_job_application_quarter_career():
    # # Định nghĩa năm cần thống kê
    # year = 2024
    #
    # # Tính toán ngày bắt đầu và kết thúc của từng quý
    # quarters = [
    #     (1, datetime(year, 1, 1), datetime(year, 3, 31)),
    #     (2, datetime(year, 4, 1), datetime(year, 6, 30)),
    #     (3, datetime(year, 7, 1), datetime(year, 9, 30)),
    #     (4, datetime(year, 10, 1), datetime(year, 12, 31))
    # ]
    # # Tạo một từ điển để lưu trữ kết quả của từng quý
    # quarterly_report = {}
    # # Truy vấn thống kê số lượng sinh viên nộp đơn ứng tuyển theo từng ngành nghề và từng quý
    # for quarter, quarter_start, quarter_end in quarters:
    #     applications_in_quarter = JobApplication.objects.filter(date__gte=quarter_start, date__lte=quarter_end,
    #                                                             is_student=True).values('recruitment__career__name').annotate(total_applications=Count('id')).order_by('-total_applications')
    #     quarterly_report[quarter] = applications_in_quarter
    #
    # return quarterly_report

    # return JobApplication.objects.filter(is_student=True).annotate(quarter=ExtractQuarter('date'), year=ExtractYear('date')).values('recruiment__career__name', 'quarter', 'year').annotate(total_applications=Count('id'))

    queryset = JobApplication.objects.filter(is_student=True) \
        .annotate(quarter=ExtractQuarter('date'), year=ExtractYear('date')) \
        .values('recruitment__career__name', 'quarter', 'year') \
        .annotate(total_applications=Count('id'))

    return queryset
