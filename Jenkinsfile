pipeline {
    agent any

    stages {
        stage('Clone Code') {
            steps {
                // Clone project từ repository
                git branch: 'master', url: 'https://github.com/TranDangMyTien/JobPortalApp.git'
            }
        }
        stage('Docker Build') {
            steps {
                script {
                    // Xây dựng Docker image với tag
                    def imageName = "trandangmytien/ou-job:latest"
                    // Sử dụng lệnh bat cho Windows
                    bat "docker build -t ${imageName} ."
                }
            }
        }
        stage('Docker Hub') {
            steps {
                withDockerRegistry(credentialsId: 'docker-hub', url: 'https://index.docker.io/v1/') {
                    // Đẩy image lên Docker Hub
                    // Sử dụng lệnh bat cho Windows
                    bat "docker push ${imageName}"
                }
            }
        }
    }
}
