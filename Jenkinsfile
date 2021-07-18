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
                withCredentials([file(credentialsId: 'feedback_bot', variable: 'feedback_main_env')]) {
                    sh "pwd"
                    sh "cp \"${feedback_main_env}\" \"feedback-bot-dev.env\""

                    echo "Deploying and Building..."
                    sh "sendNotification '#Feedback_Bot 🛠 Building New Container #${BUILD_NUMBER}'"
                    sh "docker-compose build"
                    sh "sendNotification '#Feedback_Bot ⛔️️ Stopping Previous Container #${BUILD_NUMBER}'"
                    echo "Stopping previous container..."
                    sh "docker-compose down"
                    sh "sendNotification '#Feedback_Bot 🐳 Upping New Container #${BUILD_NUMBER}'"
                    sh "docker-compose up -d"
                    echo "Deployed!"
                }
            }
        }

        stage("Deploy Dev") {
            when {
                branch "dev"
            }

            steps {
                withCredentials([file(credentialsId: 'feedback_bot_dev', variable: 'feedback_dev_env')]) {
                    sh "pwd"
                    sh "cp \"${feedback_dev_env}\" \"feedback-bot.env\""

                    echo "Deploying and Building..."
                    sh "sendNotification '#Feedback_Bot_Dev 🛠 Building New Container #${BUILD_NUMBER}'"
                    sh "docker-compose -f docker-compose-dev.yml build"
                    sh "sendNotification '#Feedback_Bot_Dev ⛔️️ Stopping Previous Container #${BUILD_NUMBER}'"
                    echo "Stopping previous container..."
                    sh "docker-compose -f docker-compose-dev.yml down"
                    sh "sendNotification '#Feedback_Bot_Dev 🐳 Upping New Container #${BUILD_NUMBER}'"
                    sh "docker-compose -f docker-compose-dev.yml up -d"
                    echo "Deployed!"
                }
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
