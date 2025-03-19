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
                
                // 작업에 필요한 디렉토리 생성
                sh 'mkdir -p nginx/conf.d'
                
                // 기본 upstream 설정 파일 준비
                sh """
                echo "upstream backend { server ${APP_NAME}-blue-backend:${BLUE_PORT_BACKEND}; }" > nginx/conf.d/upstream_blue.conf
                echo "upstream backend { server ${APP_NAME}-green-backend:${GREEN_PORT_BACKEND}; }" > nginx/conf.d/upstream_green.conf
                """
            }
        }

        stage('Docker Login') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh 'echo "$DOCKER_PASSWORD" | docker login -u $DOCKER_USERNAME --password-stdin'
                    }
                }
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
            sh 'docker logout'
            sh 'docker image prune -f'
            archiveArtifacts artifacts: 'deploy-info.txt', allowEmptyArchive: true
            // 성공 후 마지막에 작업공간 정리
            cleanWs()
        }
        failure {
            script {
                echo "배포 실패! 이전 환경으로 롤백합니다."
                // 실패 시 롤백 작업 수행 전 로그아웃/이미지 정리는 하지 않음
                rollbackToIdleEnvironment()
                cleanupFailedDeployment()
                sh 'docker logout'
                sh 'docker image prune -f'
                archiveArtifacts artifacts: 'deploy-info.txt', allowEmptyArchive: true
            }
            // 모든 작업 완료 후 마지막에 작업공간 정리
            cleanWs()
        }
    }
}

// 이미지 빌드 및 푸시 함수
def buildAndPushImage(String imageName, String context) {
    try {
        def image = docker.build(
            "${imageName}:${GIT_COMMIT_SHORT}",
            "--no-cache ${context}"
        )

        image.push()
        image.push('latest')
    } catch (Exception e) {
        echo "이미지 빌드 중 오류 발생: ${e.message}"
        error "이미지 빌드 및 푸시 실패"
    }
}

def determineEnvironment() {
    try {
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
    } catch (Exception e) {
        echo "환경 결정 중 오류 발생: ${e.message}"
        env.DEPLOY_ENV = 'blue'  // 기본값 설정
        env.IDLE_ENV = 'green'
        echo "기본 환경으로 설정: ${env.DEPLOY_ENV}"
    }
}

def deployNewEnvironment() {
    try {
        // 기존 컨테이너 제거 (있는 경우)
        sh """
        docker-compose -f docker-compose.yml -f docker-compose.${env.DEPLOY_ENV}.yml down || true
        """

        // 새 버전 배포 (레지스트리에서 이미지 가져와 사용)
        sh """
        # 이미지 풀
        docker pull ${DOCKER_REGISTRY}/${APP_NAME}-backend:latest
        docker pull ${DOCKER_REGISTRY}/${APP_NAME}-frontend:latest
        
        # Docker Compose로 배포
        docker-compose -f docker-compose.yml -f docker-compose.${env.DEPLOY_ENV}.yml up -d
        """
        
        // 프론트엔드 빌드 파일이 볼륨에 복사될 시간을 주기
        echo "프론트엔드 빌드 파일 복사를 위해 10초 대기..."
        sleep 10
        
        echo "새 환경(${env.DEPLOY_ENV}) 배포 완료 - 이미지 버전: latest (커밋: ${GIT_COMMIT_SHORT})"
    } catch (Exception e) {
        echo "새 환경 배포 중 오류 발생: ${e.message}"
        error "환경 배포 실패"
    }
}

def testNewEnvironment() {
    try {
        // 배포 후 상태 확인 시간 부여
        echo "배포된 환경 안정화를 위해 15초 대기..."
        sleep 15
        
        // 백엔드 및 프론트엔드 상태 확인
        sh """
        # 백엔드 헬스체크
        curl -f http://localhost:${env.DEPLOY_PORT_BACKEND}/api/health || { echo "백엔드 헬스체크 실패"; exit 1; }
        """
        
        sh """
        # 프론트엔드 헬스체크
        docker exec ${APP_NAME}-${env.DEPLOY_ENV}-frontend ls -la /usr/share/nginx/html/ | grep -q "index.html" || { echo "프론트엔드 헬스체크 실패"; exit 1; }
        """
        
        echo "새 환경(${env.DEPLOY_ENV}) 테스트 완료"
    } catch (Exception e) {
        echo "환경 테스트 중 오류 발생: ${e.message}"
        error "환경 테스트 실패"
    }
}

def switchTraffic() {
    try {
        // 무중단 배포를 위한 upstream 설정 교체 방식
        // 기존 upstream 파일을 백업 (롤백용)
        sh """
        docker exec ${NGINX_CONTAINER} cp /etc/nginx/conf.d/upstream.conf /etc/nginx/conf.d/upstream.conf.backup || true
        """
        
        // 새 환경의 upstream 파일 복사 - Resource busy 오류 방지를 위해 cp 명령 사용
        sh """
        # 새 upstream 설정 파일 생성
        echo "upstream backend { server ${APP_NAME}-${env.DEPLOY_ENV}-backend:${env.DEPLOY_PORT_BACKEND}; }" > nginx/conf.d/upstream.conf
        
        # 직접 컨테이너에 복사
        docker cp nginx/conf.d/upstream.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/upstream.conf
        """

        // Nginx 설정 리로드 (무중단)
        sh "docker exec ${NGINX_CONTAINER} nginx -s reload"

        echo "트래픽이 ${env.DEPLOY_ENV} 환경으로 전환되었습니다."
    } catch (Exception e) {
        echo "트래픽 전환 중 오류 발생: ${e.message}"
        error "트래픽 전환 실패"
    }
}

def logDeploymentInfo() {
    def deploymentTime = new Date().format("yyyy-MM-dd HH:mm:ss")
    echo "배포 완료 시간: ${deploymentTime}"
    echo "배포된 버전: latest (커밋: ${GIT_COMMIT_SHORT})"
}

def cleanupIdleEnvironment() {
    try {
        echo "이전 환경(${env.IDLE_ENV}) 정리를 시작합니다..."
        sh """
        docker stop ${APP_NAME}-${env.IDLE_ENV}-backend ${APP_NAME}-${env.IDLE_ENV}-frontend || true
        docker rm ${APP_NAME}-${env.IDLE_ENV}-backend ${APP_NAME}-${env.IDLE_ENV}-frontend || true
        """
        echo "이전 환경(${env.IDLE_ENV}) 정리가 완료되었습니다."
    } catch (Exception e) {
        echo "이전 환경 정리 중 오류 발생: ${e.message}"
    }
}

def rollbackToIdleEnvironment() {
    try {
        if (env.IDLE_ENV) {
            // nginx 디렉토리 확인 및 생성
            sh 'mkdir -p nginx/conf.d'
            
            // 롤백을 위한 upstream 설정 생성 및 적용 - Resource busy 오류 방지를 위해 cp 명령 사용
            sh """
            # 롤백을 위한 upstream 설정 생성
            echo "upstream backend { server ${APP_NAME}-${env.IDLE_ENV}-backend:${env.IDLE_ENV == 'blue' ? BLUE_PORT_BACKEND : GREEN_PORT_BACKEND}; }" > nginx/conf.d/upstream.conf
            
            # 직접 컨테이너에 복사
            docker cp nginx/conf.d/upstream.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/upstream.conf
            """
            
            // Nginx 설정 리로드
            sh "docker exec ${NGINX_CONTAINER} nginx -s reload || true"
            
            echo "트래픽을 이전 환경(${env.IDLE_ENV})으로 롤백했습니다."
        }
    } catch (Exception e) {
        echo "롤백 중 오류 발생: ${e.message}"
    }
}

def cleanupFailedDeployment() {
    try {
        sh """
        docker stop ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
        docker rm ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
        """
    } catch (Exception e) {
        echo "실패한 배포 정리 중 오류 발생: ${e.message}"
    }
}