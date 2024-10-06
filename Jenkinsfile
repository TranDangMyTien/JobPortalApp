pipeline {
    agent any

    environment {
        IMAGE_NAME = "trandangmytien/ou-job:latest"
        DOCKER_CREDENTIALS_ID = 'dockerPass'  // ID credentials cho Docker Hub
    }

    stages {
        stage('Clone Code') {
            steps {
                git branch: 'master', url: 'https://github.com/TranDangMyTien/JobPortalApp.git'
            }
        }

        stage('Create .env File') {
            steps {
                script {
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
                    writeFile file: '.env', text: envContent
                }
            }
        }

//         stage('Build') {
//             steps {
//                 script {
//                     echo "Database Name is ${env.DATABASE_NAME}"
//                     echo "Database User is ${env.DATABASE_USER}"
//                     echo "Database Host is ${env.DATABASE_HOST}"
//                     echo "Cloud Name is ${env.CLOUD_NAME}"
//                     echo "OAuth2 ID is ${env.OAUTH2_ID}"
//                     echo "Email User is ${env.EMAIL_USER}"
//                     echo "Django Settings Module is ${env.DJANGO_SETTINGS_MODULE}"
//                 }
//             }
//         }

        stage('Check Entrypoint') {
            steps {
                script {
                    bat 'type entrypoint.sh'
                    bat 'dir'
                }
            }
        }


//     Kiểm tra Docker
        stage('Check Docker Access') {
            steps {
                script {
                    bat 'docker --version'
                    bat 'docker ps'
                }
            }
        }



//         stage('Cleanup Docker') {
//             steps {
//                 script {
//                     bat 'docker ps -q --filter "name=django_ou_job" | findstr /v "^$" && docker rm -f django_ou_job || echo "Container django_ou_job not found"'
//                     bat 'docker ps -q --filter "name=redis_ou_job" | findstr /v "^$" && docker rm -f redis_ou_job || echo "Container redis_ou_job not found"'
//                     bat 'docker ps -q --filter "name=mysql_ou_job" | findstr /v "^$" && docker rm -f mysql_ou_job || echo "Container mysql_ou_job not found"'
//                 }
//             }
//         }

        stage('Docker Compose Build') {
            steps {
                script {
                    bat 'docker-compose build || (echo "Docker Compose build failed" && exit 1)'
                }
            }
        }

        stage('Docker Compose Up') {
            steps {
                script {
                    bat 'docker-compose up -d || (echo "Docker Compose up failed" && exit 1)'
                    sleep(time: 90, unit: 'SECONDS')
                }
            }
        }

        stage('Check Container Status') {
            steps {
                script {
                    bat 'docker-compose ps'
                }
            }
        }

        stage('Check Django Logs') {
            steps {
                script {
                    bat 'docker-compose logs django || echo "Failed to retrieve Django logs"'
                }
            }
        }


        stage('Docker Push to Hub') {
            steps {
                script {
                    withDockerRegistry(credentialsId: "${DOCKER_CREDENTIALS_ID}", url: 'https://index.docker.io/v1/') {
                        bat "docker tag ${IMAGE_NAME} trandangmytien/ou-job:latest"
                        bat "docker push trandangmytien/ou-job:latest"
                    }
                }
            }
        }
    }
    post {
        always {
            script {
                def downResult = bat(returnStatus: true, script: 'docker-compose down')
                if (downResult != 0) {
                    echo "Docker Compose down failed, but ignored"
                } else {
                    echo "Docker Compose down completed successfully"
                }
            }
        }
        failure {
            echo 'The pipeline failed. Check the logs for details.'
        }
    }
}

// Nhớ bật Docker Desktop lên và xóa đi cái cũ trước đó

// docker-compose down giúp dọn dẹp môi trường, đảm bảo không có container hoặc network cũ còn
// sót lại.
// Tránh xung đột giữa các lần chạy pipeline.
// Giải phóng tài nguyên hệ thống.