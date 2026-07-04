pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {
        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Train Model') {
            steps {
                sh '''
                    . venv/bin/activate
                    python3 train.py
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest -q
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t customer-churn-mlops:latest .
                '''
            }
        }

        stage('Create and test Container') {
            steps {
                sh '''
                    # Remove old test container if it exists
                    docker rm -f churn-api-test || true

                    docker run -d -p 8000:8000 --name churn-api-test customer-churn-mlops:latest

                    # Give FastAPI a few seconds to start
                    sleep 5

                    # Fail Jenkins if /health does not return a successful response
                    curl -f http://127.0.0.1:8000/health

                    docker stop churn-api-test
                    docker rm churn-api-test
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKERHUB_USERNAME',
                    passwordVariable: 'DOCKERHUB_PASSWORD'
                )]) {
                    sh '''
                        printf "%s" "$DOCKERHUB_PASSWORD" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
                        docker tag customer-churn-mlops:latest shuvamrs/customer-churn-mlops:latest
                        docker push shuvamrs/customer-churn-mlops:latest
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ Jenkins pipeline completed successfully. Docker image was built, tested, and pushed.'
        }

        failure {
            echo '❌ Jenkins pipeline failed.'
        }
    }
}