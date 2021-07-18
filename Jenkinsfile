pipeline {
    agent any

    environment {
        PATH = "$PATH:/usr/bin"
    }

    stages {
        stage("Deploy Prod") {
            when {
                branch "main"
            }

            steps {
                echo "Deploying and Building..."
                sh "sendNotification '#Feedback_Bot 🛠 Building New Container...'"
                sh "docker-compose build"
                sh "sendNotification '#Feedback_Bot ⛔️️ Stopping Previous Container...'"
                echo "Stopping previous container..."
                sh "docker-compose down"
                sh "sendNotification '#Feedback_Bot 🐳 Upping New Container...'"
                sh "docker-compose up -d"
                echo "Deployed!"
            }
        }

        stage("Deploy Dev") {
            when {
                branch "dev"
            }

            steps {
                echo "Deploying and Building..."
                sh "sendNotification '#Feedback_Bot_Dev 🛠 Building New Container...'"
                sh "docker-compose -f docker-compose-dev.yml build"
                sh "sendNotification '#Feedback_Bot_Dev ⛔️️ Stopping Previous Container...'"
                echo "Stopping previous container..."
                sh "docker-compose -f docker-compose-dev.yml down"
                sh "sendNotification '#Feedback_Bot_Dev 🐳 Upping New Container...'"
                sh "docker-compose -f docker-compose-dev.yml up -d"
                echo "Deployed!"
            }
        }
    }

    post {
        success {
            sh "sendNotification '#Feedback_Bot 🥃 Deploy Succeed 😍💕😋😎️'"
        }
        failure {
            sh "sendNotification '#Feedback_Bot 🛑 Deploy Failed  😩😑😖😳'"
        }
    }
}
