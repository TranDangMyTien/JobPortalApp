import os
import django
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.preprocessing import LabelEncoder
from jobs.models import (
    JobApplication,
    RecruitmentPost,
    Employer,
    Applicant,
    Career,
)

# Set the environment variable for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobPortal.settings')
# django.setup()

def get_data():
    """Lấy dữ liệu từ các model Django và chuyển đổi thành DataFrame."""
    applications = pd.DataFrame(list(JobApplication.objects.all().values()))
    posts = pd.DataFrame(list(RecruitmentPost.objects.all().values()))
    employers = pd.DataFrame(list(Employer.objects.all().values()))
    applicants = pd.DataFrame(list(Applicant.objects.all().values()))
    careers = pd.DataFrame(list(Career.objects.all().values()))

    return applications, posts, employers, applicants, careers

def analyze_application_trends(applications):
    """Phân tích xu hướng đơn xin việc theo tháng."""
    applications['date'] = pd.to_datetime(applications['date'])
    monthly_trends = applications.resample('ME', on='date').count()['id']
    return monthly_trends

def predict_application_success_rate(applications):
    """Dự đoán tỷ lệ thành công của đơn xin việc."""
    applications['is_accepted'] = applications['status_id'].apply(lambda x: 1 if x == 1 else 0)

    features = applications[['applicant_id', 'recruitment_id', 'is_student']].copy()
    target = applications['is_accepted']

    le_applicant = LabelEncoder()
    le_recruitment = LabelEncoder()
    features['applicant_id'] = le_applicant.fit_transform(features['applicant_id'])
    features['recruitment_id'] = le_recruitment.fit_transform(features['recruitment_id'])

    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    return accuracy

def predict_salary_for_recruitment(posts):
    """Dự đoán lương dựa trên các tính năng của bài đăng tuyển dụng."""
    features = posts[['quantity', 'career_id']].copy()
    target = posts['salary']

    le_career = LabelEncoder()
    features['career_id'] = le_career.fit_transform(features['career_id'])

    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "AdaBoost": AdaBoostRegressor(n_estimators=100, random_state=42),
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        results[name] = mse

    return results

def predict_application_count(posts, applications):
    """Dự đoán số lượng đơn xin dựa trên các tính năng của bài đăng tuyển dụng."""
    application_count_series = applications.groupby('recruitment_id').size()
    posts['application_count'] = posts['id'].map(application_count_series).fillna(0)

    features = posts[['quantity', 'career_id']].copy()
    target = posts['application_count']

    le_career = LabelEncoder()
    features['career_id'] = le_career.fit_transform(features['career_id'])

    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)

    return mse

def predict_salary_range(posts):
    """Dự đoán khoảng lương cho các bài đăng tuyển dụng dựa trên nhiều thuật toán khác nhau."""
    features = posts[['quantity', 'career_id']].copy()
    target = posts['salary']

    le_career = LabelEncoder()
    features['career_id'] = le_career.fit_transform(features['career_id'])

    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    models = {
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        results[name] = mse

    return results

# def save_results(monthly_trends, success_rate_accuracy, salary_mse_results, application_count_mse, salary_range_mse_results):
#     """Lưu kết quả vào tệp CSV."""
#     results = {
#         "Monthly Trends": monthly_trends,
#         "Success Rate Accuracy": success_rate_accuracy,
#         "Application Count MSE": application_count_mse,
#         "Salary MSE": salary_mse_results,
#         "Salary Range MSE": salary_range_mse_results
#     }
#
#     # Ensure all results are in a consistent format for DataFrame
#     results_df = pd.DataFrame.from_dict({
#         "Monthly Trends": monthly_trends,
#         "Success Rate Accuracy": [success_rate_accuracy],
#         "Application Count MSE": [application_count_mse],
#         **{f"{model} MSE": [mse] for model, mse in salary_mse_results.items()},
#         **{f"{model} Range MSE": [mse] for model, mse in salary_range_mse_results.items()},
#     })
#
#     results_df.to_csv('job_portal_analysis_results.csv', index=False)

def main():
    """Chương trình chính để thực hiện phân tích và dự đoán."""
    applications, posts, employers, applicants, careers = get_data()

    # Phân tích xu hướng đơn xin
    monthly_trends = analyze_application_trends(applications)
    print("Xu hướng đơn xin theo tháng:\n", monthly_trends)

    # Dự đoán tỷ lệ thành công của đơn xin
    success_rate_accuracy = predict_application_success_rate(applications)
    print(f"Độ chính xác của việc dự đoán tỷ lệ thành công đơn xin: {success_rate_accuracy:.2f}")

    # Dự đoán lương cho các bài đăng
    salary_mse_results = predict_salary_for_recruitment(posts)
    for model, mse in salary_mse_results.items():
        print(f"MSE của {model}: {mse:.2f}")

    # Dự đoán số lượng đơn xin cho các bài đăng
    application_count_mse = predict_application_count(posts, applications)
    print(f"Mean Squared Error của số lượng đơn xin dự đoán: {application_count_mse:.2f}")

    # Dự đoán khoảng lương với nhiều thuật toán
    salary_range_mse_results = predict_salary_range(posts)
    for model, mse in salary_range_mse_results.items():
        print(f"MSE của {model}: {mse:.2f}")

    # Lưu kết quả vào tệp CSV
    # save_results(monthly_trends, success_rate_accuracy, salary_mse_results, application_count_mse, salary_range_mse_results)

    return {
        "monthly_trends": monthly_trends,
        "success_rate_accuracy": success_rate_accuracy,
        "salary_mse_results": salary_mse_results,
        "application_count_mse": application_count_mse,
        "salary_range_mse_results": salary_range_mse_results
    }

if __name__ == "__main__":
    main()
