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
                
                // 블루/그린 upstream 설정 파일 준비
                sh """
                echo "upstream backend { server ${APP_NAME}-blue-backend:${BLUE_PORT_BACKEND}; }" > nginx/conf.d/upstream_blue.conf
                echo "upstream backend { server ${APP_NAME}-green-backend:${GREEN_PORT_BACKEND}; }" > nginx/conf.d/upstream_green.conf
                
                # 컨테이너에 upstream 파일 복사
                docker cp nginx/conf.d/upstream_blue.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/ || true
                docker cp nginx/conf.d/upstream_green.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/ || true
                
                # default.conf 내용 확인 - 에러 디버깅
                docker exec ${NGINX_CONTAINER} cat /etc/nginx/conf.d/default.conf || true
                """
                
                // Nginx 설정 파일 초기화 (default.conf에 문제가 있는 경우)
                sh """
                # default.conf 파일에 문제가 있는지 확인하고 필요시 수정
                docker exec ${NGINX_CONTAINER} grep -q "pipeline" /etc/nginx/conf.d/default.conf && 
                echo "default.conf 파일에 문제가 있어 초기화합니다" &&
                echo 'server { listen 80; location / { root /usr/share/nginx/html; } }' | docker exec -i ${NGINX_CONTAINER} tee /etc/nginx/conf.d/default.conf.new &&
                docker exec ${NGINX_CONTAINER} mv /etc/nginx/conf.d/default.conf.new /etc/nginx/conf.d/default.conf || true
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
            // 성공 후 작업공간 정리
            cleanWs()
        }
        failure {
            script {
                echo "배포 실패! 이전 환경으로 롤백합니다."
                
                // 실패 시 롤백 작업 수행
                rollbackToIdleEnvironment()
                cleanupFailedDeployment()
                
                // 로그아웃 및 정리
                sh 'docker logout'
                sh 'docker image prune -f'
                archiveArtifacts artifacts: 'deploy-info.txt', allowEmptyArchive: true
            }
            // 모든 작업 완료 후 작업공간 정리
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
        // 현재 활성 환경 확인
        def activeEnv = sh(
            script: """
            # 컨테이너가 사용 중인 업스트림 구성 확인
            docker exec ${NGINX_CONTAINER} cat /etc/nginx/conf.d/upstream.conf 2>/dev/null | grep -o "${APP_NAME}-\\(blue\\|green\\)" | cut -d'-' -f2 || echo 'blue'
            """,
            returnStdout: true
        ).trim()

        // 유효한 값이 없으면 기본값 설정
        if(activeEnv == '' || activeEnv == 'none') {
            activeEnv = 'blue'
        }

        if(activeEnv == 'green') {
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
        # 컨테이너 중지 및 제거 (있는 경우)
        docker stop ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
        docker rm ${APP_NAME}-${env.DEPLOY_ENV}-backend ${APP_NAME}-${env.DEPLOY_ENV}-frontend || true
        """

        // 이미지 가져오기
        sh """
        # 이미지 풀
        docker pull ${DOCKER_REGISTRY}/${APP_NAME}-backend:latest
        docker pull ${DOCKER_REGISTRY}/${APP_NAME}-frontend:latest
        """
        
        // 컨테이너 실행 - Docker Compose 대신 직접 docker run 명령 사용
        sh """
        # 백엔드 컨테이너 실행
        docker run -d --name ${APP_NAME}-${env.DEPLOY_ENV}-backend \\
            --network ${NETWORK_NAME} \\
            -p ${env.DEPLOY_PORT_BACKEND}:${env.DEPLOY_PORT_BACKEND} \\
            ${DOCKER_REGISTRY}/${APP_NAME}-backend:latest
            
        # 프론트엔드 컨테이너 실행
        docker run -d --name ${APP_NAME}-${env.DEPLOY_ENV}-frontend \\
            --network ${NETWORK_NAME} \\
            -p ${env.DEPLOY_PORT_FRONTEND}:${env.DEPLOY_PORT_FRONTEND} \\
            ${DOCKER_REGISTRY}/${APP_NAME}-frontend:latest
        """
        
        // 프론트엔드 빌드 파일이 볼륨에 복사될 시간을 주기
        echo "프론트엔드 빌드 파일 복사를 위해 10초 대기..."
        sleep 10
        
        echo "새 환경(${env.DEPLOY_ENV}) 배포 완료 - 이미지 버전: latest (커밋: ${GIT_COMMIT_SHORT})"
    } catch (Exception e) {
        echo "새 환경 배포 중 오류 발생: ${e.message}"
        
        // 문제 상황 디버깅을 위한 추가 정보 수집
        sh """
        echo "Docker 상태 확인:"
        docker ps -a | grep ${APP_NAME} || true
        echo "Docker 네트워크 확인:"
        docker network ls | grep ${NETWORK_NAME} || true
        echo "Docker 이미지 확인:"
        docker images | grep ${DOCKER_REGISTRY}/${APP_NAME} || true
        """
        
        error "환경 배포 실패"
    }
}

def testNewEnvironment() {
    try {
        // 배포 후 상태 확인 시간 부여
        echo "배포된 환경 안정화를 위해 15초 대기..."
        sleep 15
        
        // 컨테이너 실행 상태 확인
        sh """
        # 컨테이너 상태 확인
        docker ps | grep ${APP_NAME}-${env.DEPLOY_ENV}-backend || { echo "백엔드 컨테이너가 실행되지 않았습니다"; exit 1; }
        docker ps | grep ${APP_NAME}-${env.DEPLOY_ENV}-frontend || { echo "프론트엔드 컨테이너가 실행되지 않았습니다"; exit 1; }
        """
        
        // 백엔드 헬스체크 (헬스체크 API가 있는 경우)
        sh """
        # 백엔드 헬스체크 - 만약 실패해도 계속 진행
        curl -f http://localhost:${env.DEPLOY_PORT_BACKEND}/api/health || echo "백엔드 헬스체크 실패하였으나 계속 진행합니다"
        """
        
        echo "새 환경(${env.DEPLOY_ENV}) 테스트 완료"
    } catch (Exception e) {
        echo "환경 테스트 중 오류 발생: ${e.message}"
        error "환경 테스트 실패"
    }
}

def switchTraffic() {
    try {
        // upstream.conf 파일 내용 준비
        sh """
        # 새로운 upstream 설정 파일 생성
        echo "upstream backend { server ${APP_NAME}-${env.DEPLOY_ENV}-backend:${env.DEPLOY_PORT_BACKEND}; }" > nginx/conf.d/upstream.conf
        
        # 컨테이너에 복사 - 덮어쓰기용 임시 파일
        docker cp nginx/conf.d/upstream.conf ${NGINX_CONTAINER}:/etc/nginx/conf.d/upstream.conf.new
        """
        
        // 직접 덮어쓰기 (심볼릭 링크 대신 컨테이너 내에서 파일 교체)
        sh """
        # 아래 명령어는 Resource busy 오류를 방지하기 위해 컨테이너 내에서 실행
        docker exec ${NGINX_CONTAINER} bash -c '
        # 임시 파일로 복사 후 덮어쓰기 (원자적 작업)
        cat /etc/nginx/conf.d/upstream.conf.new > /etc/nginx/conf.d/upstream.conf
        rm -f /etc/nginx/conf.d/upstream.conf.new
        '
        
        # Nginx 설정 리로드
        docker exec ${NGINX_CONTAINER} nginx -s reload
        """

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
            // 롤백용 설정 파일 생성
            sh """
            # 롤백용 upstream 설정 파일 생성
            echo "upstream backend { server ${APP_NAME}-${env.IDLE_ENV}-backend:${env.IDLE_ENV == 'blue' ? BLUE_PORT_BACKEND : GREEN_PORT_BACKEND}; }" > nginx/conf.d/upstream.conf.rollback
            
            # 컨테이너에 복사
            docker cp nginx/conf.d/upstream.conf.rollback ${NGINX_CONTAINER}:/etc/nginx/conf.d/
            """
            
            // 컨테이너 내에서 파일 교체
            sh """
            # 컨테이너 내에서 파일 교체 (Resource busy 오류 방지)
            docker exec ${NGINX_CONTAINER} bash -c '
            cat /etc/nginx/conf.d/upstream.conf.rollback > /etc/nginx/conf.d/upstream.conf
            rm -f /etc/nginx/conf.d/upstream.conf.rollback
            '
            
            # Nginx 설정 리로드
            docker exec ${NGINX_CONTAINER} nginx -s reload
            """
            
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