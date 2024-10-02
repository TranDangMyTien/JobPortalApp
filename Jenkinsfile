pipeline {
    agent any

    environment {
        IMAGE_NAME = "trandangmytien/ou-job:latest"
        DOCKER_CREDENTIALS_ID = 'docker-hub'  // ID credentials cho Docker Hub
    }

    stages {
        stage('Clone Code') {
            steps {
                // Clone project từ repository
                git branch: 'master', url: 'https://github.com/TranDangMyTien/JobPortalApp.git'
            }
        }
        stage('Create .env File') {
            steps {
                script {
                    // Tạo file .env từ các biến môi trường đã định nghĩa trong Jenkins
                    def envContent = """
                    DATABASE_NAME=${env.DATABASE_NAME}
                    DATABASE_USER=${env.DATABASE_USER}
                    DATABASE_PASSWORD=${env.DATABASE_PASSWORD}
                    DATABASE_HOST=${env.DATABASE_HOST}
                    CLOUD_NAME=${env.CLOUD_NAME}
                    CLOUD_KEY=${env.CLOUD_KEY}
                    CLOUD_SECRET=${env.CLOUD_SECRET}
                    OAUTH2_ID=${env.OAUTH2_ID}
                    OAUTH2_SECRET=${env.OAUTH2_SECRET}
                    EMAIL_BACKEND=${env.EMAIL_BACKEND}
                    EMAIL_HOST=${env.EMAIL_HOST}
                    EMAIL_USER=${env.EMAIL_USER}
                    EMAIL_PASSWORD=${env.EMAIL_PASSWORD}
                    SECRET_KEY=${env.SECRET_KEY}
                    DJANGO_SETTINGS_MODULE=${env.DJANGO_SETTINGS_MODULE}
                    """

                    // Ghi nội dung vào file .env trong thư mục gốc của dự án
                    writeFile file: '.env', text: envContent
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    // In ra các biến môi trường
                    echo "Database Name is ${env.DATABASE_NAME}"
                    echo "Database User is ${env.DATABASE_USER}"
                    echo "Database Host is ${env.DATABASE_HOST}"
                    echo "Cloud Name is ${env.CLOUD_NAME}"
                    echo "OAuth2 ID is ${env.OAUTH2_ID}"
                    echo "Email User is ${env.EMAIL_USER}"
                    echo "Django Settings Module is ${env.DJANGO_SETTINGS_MODULE}"

                    // In ra tất cả các biến môi trường
//                     bat 'set'
                }
            }
        }

        stage('Cleanup Docker') {
            steps {
                script {
                    // Xóa container tồn tại nếu có để tránh xung đột
                    bat 'docker rm -f django_ou_job || true'
                    bat 'docker rm -f redis_ou_job || true'
                    bat 'docker rm -f mysql_ou_job || true'
                }
            }
        }

        stage('Docker Compose Build') {
            steps {
                script {
                    // Xây dựng Docker image với docker-compose
                    bat 'docker-compose build'
                }
            }
        }
        stage('Docker Compose Up') {
            steps {
                script {
                    // Khởi động container với docker-compose
                    bat 'docker-compose up -d'
                }
            }
        }
        stage('Run Migrations') {
            steps {
                script {
                    // Chạy migrations
                    bat 'docker-compose exec django python manage.py migrate'
                }
            }
        }
        stage('Docker Push to Hub') {
            steps {
                script {
                    withDockerRegistry(credentialsId: "${DOCKER_CREDENTIALS_ID}", url: 'https://index.docker.io/v1/') {
                        // Tag và push image lên Docker Hub
                        bat "docker tag ${IMAGE_NAME} trandangmytien/ou-job:latest"
                        bat "docker push trandangmytien/ou-job:latest"
                    }
                }
            }
        }
    }
    post {
        always {
            // Tắt các container sau khi hoàn thành
            bat 'docker-compose down'
        }
    }
}
