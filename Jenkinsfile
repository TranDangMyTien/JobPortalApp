pipeline {
    agent any

    environment {
        // Đặt tên cho image Docker
        IMAGE_NAME = "trandangmytien/ou-job:latest"
        DOCKER_CREDENTIALS_ID = 'docker-hub'  // Đặt ID credentials cho Docker Hub
    }

    stages {
        stage('Clone Code') {
            steps {
                // Clone project từ repository
                git branch: 'master', url: 'https://github.com/TranDangMyTien/JobPortalApp.git'
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
