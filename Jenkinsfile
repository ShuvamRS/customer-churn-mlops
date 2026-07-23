pipeline {
    agent any

    triggers {
        githubPush()
    }

    environment {
        AWS_REGION = 'us-west-1'
        ECR_REPO_NAME = 'customer-churn-mlops'
        EKS_CLUSTER_NAME = 'customer-churn-eks'
        S3_BUCKET_NAME = 'customer-churn-mlops-models-shuvamrs'
        MODEL_S3_KEY = 'model.joblib'
        TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Setup') {
            steps {
                script {
                    env.IMAGE = sh(
                        script: "aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${AWS_REGION} --query 'repositories[0].repositoryUri' --output text",
                        returnStdout: true
                    ).trim()
                }

                sh '''
                    aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
                '''
            }
        }

        stage('Train Model and Upload to S3') {
            steps {
                sh '''
                    docker run --rm --network host \
                      -v "$PWD":/workspace \
                      -w /workspace \
                      -e S3_BUCKET_NAME="$S3_BUCKET_NAME" \
                      -e MODEL_S3_KEY="$MODEL_S3_KEY" \
                      -e AWS_REGION="$AWS_REGION" \
                      python:3.12-slim \
                      bash -c "pip install --no-cache-dir -r requirements.txt && python train.py"

                    aws s3 ls s3://$S3_BUCKET_NAME/$MODEL_S3_KEY
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    docker run --rm --network host \
                      -v "$PWD":/workspace \
                      -w /workspace \
                      -e S3_BUCKET_NAME="$S3_BUCKET_NAME" \
                      -e MODEL_S3_KEY="$MODEL_S3_KEY" \
                      -e AWS_REGION="$AWS_REGION" \
                      python:3.12-slim \
                      bash -c "pip install --no-cache-dir -r requirements.txt && pytest -q"
                '''
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                    docker build -t $IMAGE:$TAG -t $IMAGE:latest .
                '''
            }
        }

        stage('Test Container') {
            steps {
                sh '''
                    docker rm -f churn-api-test || true

                    docker run -d \
                      --name churn-api-test \
                      --network host \
                      -e S3_BUCKET_NAME="$S3_BUCKET_NAME" \
                      -e MODEL_S3_KEY="$MODEL_S3_KEY" \
                      -e AWS_REGION="$AWS_REGION" \
                      $IMAGE:$TAG

                    sleep 10

                    docker logs churn-api-test
                    curl -f http://127.0.0.1:8000/health

                    docker rm -f churn-api-test
                '''
            }
        }

        stage('Push Image') {
            steps {
                sh '''
                    ECR_REGISTRY=$(echo $IMAGE | cut -d/ -f1)

                    aws ecr get-login-password --region $AWS_REGION | \
                      docker login --username AWS --password-stdin $ECR_REGISTRY

                    docker push $IMAGE:$TAG
                    docker push $IMAGE:latest
                '''
            }
        }

        stage('Deploy to EKS') {
            steps {
                sh '''
                    kubectl apply -f k8s/configmap.yaml
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml

                    kubectl set image deployment/customer-churn-deployment \
                      customer-churn-api=$IMAGE:$TAG

                    kubectl rollout status deployment/customer-churn-deployment --timeout=300s

                    kubectl get pods
                    kubectl get service customer-churn-service
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f churn-api-test || true
            '''
        }

        success {
            echo "Shipped $IMAGE:$TAG to EKS."
        }

        failure {
            echo 'Pipeline failed — model training, tests, image build, push, or deploy did not pass.'
        }
    }
}
