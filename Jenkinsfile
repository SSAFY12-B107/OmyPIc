pipeline {
    agent any

    environment {
        // 프로젝트 설정
        APP_NAME = "omypic"
        GIT_REPO = "https://lab.ssafy.com/s12-ai-speech-sub1/S12P21B107.git"
        
        // 블루/그린 환경 설정
        BLUE_PORT_BACKEND = "8000"
        GREEN_PORT_BACKEND = "8001"
        BLUE_PORT_FRONTEND = "3000"
        GREEN_PORT_FRONTEND = "3001"
        
        // Docker & Nginx 설정
        NETWORK_NAME = "omypic-network"
        NGINX_CONTAINER = "omypic-nginx"
        
        // Docker Registry 설정 
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKER_REGISTRY = "kst1040"
        BACKEND_IMAGE = "${DOCKER_REGISTRY}/${APP_NAME}-backend"
        FRONTEND_IMAGE = "${DOCKER_REGISTRY}/${APP_NAME}-frontend"
        
        // Git 커밋 정보
        GIT_COMMIT_SHORT = sh(
            script: "printf \$(git rev-parse --short HEAD)",
            returnStdout: true
        )
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'master']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    userRemoteConfigs: [[
                        credentialsId: 'gitlab-user-pwd',
                        url: env.GIT_REPO
                    ]]
                ])
            }
        }

        stage('Build & Push Images') {
            parallel {
                stage('Backend') {
                    when { changeset "backend/**" }
                    steps {
                        script {
                            buildAndPushImage("${BACKEND_IMAGE}", "./backend")
                        }
                    }
                }

                stage('Frontend') {
                    when { changeset "frontend/**" }
                    steps {
                        script {
                            buildAndPushImage("${FRONTEND_IMAGE}", "./frontend")
                        }
                    }
                }
            }
        }

        stage('Deploy & Switch') {
            steps {
                script {
                    // 활성 환경 확인 및 배포할 환경 결정
                    determineEnvironment()
                    
                    // 새 환경 배포
                    deployNewEnvironment()
                    
                    // 배포 후 환경 테스트
                    testNewEnvironment()
                    
                    // 트래픽 전환
                    switchTraffic()
                }
            }
        }
    }
    
    post {
        success {
            script {
                echo "배포가 성공적으로 완료되었습니다."
                logDeploymentInfo()
                cleanupIdleEnvironment()
            }
        }
        failure {
            script {
                echo "배포 실패! 이전 환경으로 롤백합니다."
                rollbackToIdleEnvironment()
                cleanupFailedDeployment()
            }
        }
        always {
            sh 'docker image prune -f'
            cleanWs()
            archiveArtifacts artifacts: 'deploy-info.txt', allowEmptyArchive: true
        }
    }
}

// 이미지 빌드 및 푸시 함수
def buildAndPushImage(String imageName, String context) {
    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
        def image = docker.build(
            "${imageName}:${GIT_COMMIT_SHORT}",
            "--cache-from ${imageName}:latest ${context}"
        )

        image.push()
        image.push('latest')
    }
}

def determineEnvironment() {
    // 현재 활성 환경 확인 (blue 또는 green)
    def activeEnv = sh(
        script: "docker exec ${NGINX_CONTAINER} cat /etc/nginx/conf.d/upstream.conf | grep -A1 'upstream backend' | grep 'server' | grep -o '${APP_NAME}-\\(blue\\|green\\)-backend' | cut -d'-' -f2 || echo 'none'",
        returnStdout: true
    ).trim()

    if(activeEnv == 'none' || activeEnv == 'green') {
        env.DEPLOY_ENV = 'blue'
        env.DEPLOY_PORT_BACKEND = BLUE_PORT_BACKEND
        env.DEPLOY_PORT_FRONTEND = BLUE_PORT_FRONTEND
        env.IDLE_ENV = 'green'
    } else {
        env.DEPLOY_ENV = 'green'
        env.DEPLOY_PORT_BACKEND = GREEN_PORT_BACKEND
        env.DEPLOY_PORT_FRONTEND = GREEN_PORT_FRONTEND
        env.IDLE_ENV = 'blue'
    }

    echo "현재 활성 환경: ${activeEnv}"
    echo "배포할 환경: ${env.DEPLOY_ENV} (백엔드: ${env.DEPLOY_PORT_BACKEND}, 프론트엔드: ${env.DEPLOY_PORT_FRONTEND})"
    
    // 배포 정보를 파일로 저장 (롤백용)
    sh """
    echo "ACTIVE_ENV=${env.DEPLOY_ENV}" > deploy-info.txt
    echo "IDLE_ENV=${env.IDLE_ENV}" >> deploy-info.txt
    echo "IMAGE_TAG=${GIT_COMMIT_SHORT}" >> deploy-info.txt
    echo "DEPLOY_TIME=\$(date '+%Y-%m-%d %H:%M:%S')" >> deploy-info.txt
    """
}

def deployNewEnvironment() {
    // 기존 컨테이너 제거 (있는 경우)
    sh """
    docker stop ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
    docker rm ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
    """

    // 새 버전 배포 (레지스트리에서 이미지 가져와 사용)
    sh """
    # 필요하면 이미지 풀
    docker pull ${DOCKER_REGISTRY}/${APP_NAME}-backend:${GIT_COMMIT_SHORT}
    docker pull ${DOCKER_REGISTRY}/${APP_NAME}-frontend:${GIT_COMMIT_SHORT}
    
    # 백엔드 컨테이너 실행
    docker run -d --name ${APP_NAME}-${env.DEPLOY_ENV}-backend \\
        -p ${env.DEPLOY_PORT_BACKEND}:8000 \\
        --network ${NETWORK_NAME} \\
        ${DOCKER_REGISTRY}/${APP_NAME}-backend:${GIT_COMMIT_SHORT}
    
    # 프론트엔드 컨테이너 실행
    docker run -d --name ${APP_NAME}-${env.DEPLOY_ENV}-frontend \\
        -p ${env.DEPLOY_PORT_FRONTEND}:80 \\
        --network ${NETWORK_NAME} \\
        ${DOCKER_REGISTRY}/${APP_NAME}-frontend:${GIT_COMMIT_SHORT}
    """
    
    echo "새 환경(${env.DEPLOY_ENV}) 배포 완료 - 이미지 버전: ${GIT_COMMIT_SHORT}"
}

def testNewEnvironment() {
    // 배포 후 상태 확인 시간 부여
    echo "배포된 환경 안정화를 위해 15초 대기..."
    sleep 15
    
    // 백엔드 및 프론트엔드 상태 확인
    sh """
    # 백엔드 헬스체크
    curl -f http://localhost:${env.DEPLOY_PORT_BACKEND}/api/health || exit 1

    # 프론트엔드 헬스체크
    curl -f http://localhost:${env.DEPLOY_PORT_FRONTEND} || exit 1
    """
    
    echo "새 환경(${env.DEPLOY_ENV}) 테스트 완료"
}

def switchTraffic() {
    // 전환 전 현재 설정 백업 (롤백용)
    sh "docker cp ${NGINX_CONTAINER}:/etc/nginx/conf.d/upstream.conf nginx/conf.d/upstream_backup.conf || true"
    
    // Nginx 업스트림 파일 교체
    sh "docker cp nginx/conf.d/upstream_${env.DEPLOY_ENV}.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/upstream.conf"

    // Nginx 설정 리로드
    sh "docker exec ${NGINX_CONTAINER} nginx -s reload"

    echo "트래픽이 ${env.DEPLOY_ENV} 환경으로 전환되었습니다."
}

def logDeploymentInfo() {
    def deploymentTime = new Date().format("yyyy-MM-dd HH:mm:ss")
    echo "배포 완료 시간: ${deploymentTime}"
    echo "배포된 버전: ${GIT_COMMIT_SHORT}"
}

def cleanupIdleEnvironment() {
    echo "이전 환경(${env.IDLE_ENV}) 정리를 시작합니다..."
    sh """
    docker stop ${APP_NAME}-${env.IDLE_ENV}-backend ${APP_NAME}-${env.IDLE_ENV}-frontend || true
    docker rm ${APP_NAME}-${env.IDLE_ENV}-backend ${APP_NAME}-${env.IDLE_ENV}-frontend || true
    """
    echo "이전 환경(${env.IDLE_ENV}) 정리가 완료되었습니다."
}

def rollbackToIdleEnvironment() {
    if (env.IDLE_ENV) {
        // 백업 파일 확인
        def backupExists = fileExists('nginx/conf.d/upstream_backup.conf')
        
        if (backupExists) {
            // 백업 파일이 있으면 이를 사용해 롤백
            sh "docker cp nginx/conf.d/upstream_backup.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/upstream.conf"
        } else {
            // 백업 파일이 없으면 이전 환경의 설정 파일 사용
            sh "docker cp nginx/conf.d/upstream_${env.IDLE_ENV}.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/upstream.conf"
        }
        
        // Nginx 설정 리로드
        sh "docker exec ${NGINX_CONTAINER} nginx -s reload || true"
        
        echo "트래픽을 이전 환경(${env.IDLE_ENV})으로 롤백했습니다."
    }
}

def cleanupFailedDeployment() {
    sh """
    docker stop ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
    docker rm ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
    """
}