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
                notifyEvents message: "#Feedback_Bot 🛠 Building New Container...", token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
                sh "docker-compose build"
                notifyEvents message: "#Feedback_Bot ⛔️️ Stopping Previous Container...", token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
                echo "Stopping previous container..."
                sh "docker-compose down"
                notifyEvents message: "#Feedback_Bot 🐳 Upping New Container...", token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
                sh "docker-compose up -d"
                echo "Deployed!"
            }
        }
    }

    stages {
        stage("Deploy Prod") {
            when {
                branch "dev"
            }

            steps {
                echo "Deploying and Building..."
                notifyEvents message: "#Feedback_Bot 🛠 Building New Container...", token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
                sh "docker-compose build -f docker-compose-dev.yml"
                notifyEvents message: "#Feedback_Bot ⛔️️ Stopping Previous Container...", token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
                echo "Stopping previous container..."
                sh "docker-compose down"
                notifyEvents message: "#Feedback_Bot 🐳 Upping New Container...", token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
                sh "docker-compose up -d"
                echo "Deployed!"
            }
        }
    }

    post {
        success {
            notifyEvents message: "#Feedback_Bot 🥃 Deploy Succeed 😍💕😋😎️", token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
        }
        failure {
            notifyEvents message: '#Feedback_Bot 🛑 Deploy Failed  😩😑😖😳', token: '7yi9o1VBd3mz-JP2JhQOICo3Y5zgPHGk'
        }
    }
}
