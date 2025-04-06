pipeline {
    agent any
    
    environment {
        DOCKER_HUB_CREDENTIALS = credentials('dockerhub-credentials')
        TARGET_ENV = ''
        CURRENT_ENV = ''
        // env.WORKSPACE를 사용하거나 기본값 제공
        WORKSPACE_PATH = "${env.WORKSPACE ?: '.'}"
        NGINX_CONF_PATH = "${env.WORKSPACE ?: '.'}/nginx/conf.d"
        DEPLOYMENT_SUCCESS = false
        BUILD_VERSION = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM', 
                  branches: [[name: "${env.gitlabSourceBranch}"]],
                  extensions: [[$class: 'PreBuildMerge', options: [fastForwardMode: 'FF', mergeRemote : 'origin', mergeTarget: "${env.gitlabTargetBranch}"
                  ]]],
                  userRemoteConfigs: [[
                    url: 'https://lab.ssafy.com/s12-ai-speech-sub1/S12P21B107.git',
                    credentialsId: 'gitlab-user-pwd'
                    ]]
                ])

                echo "소스 브랜치: ${env.gitlabSourceBranch} , 타겟 브랜치: ${env.gitlabTargetBranch}"
                echo "MR 타이틀: ${env.gitlabMergeRequestTitle}"
            }
        }
        
        stage('Determine Target Environment') {
            steps {
                script {
                    // 현재 활성 환경 확인
                    def isBlueActive = sh(
                        script: "grep -q 'server omypic-blue-backend:8000;' ${NGINX_CONF_PATH}/upstream.conf && echo 'true' || echo 'false'",
                        returnStdout: true
                    ).trim()
                    
                    // 현재 환경의 반대로 타겟 설정
                    CURRENT_ENV = isBlueActive == "true" ? "blue" : "green"
                    TARGET_ENV = isBlueActive == "true" ? "green" : "blue"
                    
                    echo "현재 환경: ${CURRENT_ENV}, 배포 대상 환경: ${TARGET_ENV}"
                }
            }
        }
        
        stage('Build Frontend') {
            agent {
                docker {
                    image 'node:22-alpine'
                    reuseNode true
                }
            }
            steps {
                dir('Frontend') {
                    sh 'npm ci'
                    sh 'npm run build'
                    
                    // 프론트엔드 Docker 이미지 빌드
                    sh "docker build -t kst1040/omypic-frontend:${TARGET_ENV}-${BUILD_NUMBER} ."
                    sh "docker tag kst1040/omypic-frontend:${TARGET_ENV}-${BUILD_NUMBER} kst1040/omypic-frontend:latest"
                }
            }
        }
        
        stage('Build Backend') {
            steps {
                dir('Backend') {
                    // 백엔드 Docker 이미지 빌드
                    sh "docker build -t kst1040/omypic-backend:${TARGET_ENV}-${BUILD_NUMBER} ."
                    sh "docker tag kst1040/omypic-backend:${TARGET_ENV}-${BUILD_NUMBER} kst1040/omypic-backend:latest"
                }
            }
        }
        
        stage('Push Images') {
            steps {
                sh 'echo $DOCKER_HUB_CREDENTIALS_PSW | docker login -u $DOCKER_HUB_CREDENTIALS_USR --password-stdin'
                
                sh "docker push kst1040/omypic-frontend:${TARGET_ENV}-${BUILD_NUMBER}"
                sh "docker push kst1040/omypic-frontend:latest"
                
                sh "docker push kst1040/omypic-backend:${TARGET_ENV}-${BUILD_NUMBER}"
                sh "docker push kst1040/omypic-backend:latest"
            }
        }
        
        stage('Deploy to Target Environment') {
            steps {
                // 대상 환경 배포 (Docker Compose 직접 실행)
                sh "docker compose -p omypic -f ${WORKSPACE_PATH}/docker-compose-${TARGET_ENV}.yml pull"
                sh "docker compose -p omypic -f ${WORKSPACE_PATH}/docker-compose-${TARGET_ENV}.yml down"
                sh "docker compose -p omypic -f ${WORKSPACE_PATH}/docker-compose-${TARGET_ENV}.yml up -d"
                
                // 배포 후 로그 확인
                sh "docker logs omypic-${TARGET_ENV}-backend --tail 50"
                sh "docker logs omypic-${TARGET_ENV}-frontend --tail 50"
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    // 배포 환경 안정화를 위한 대기
                    echo "배포 환경이 안정화될 때까지 30초 대기 중..."
                    sleep 30
                    
                    // 스크립트에 실행 권한 부여
                    sh "chmod +x ${WORKSPACE_PATH}/health-check.sh"
                    
                    // 헬스 체크 스크립트 실행 (TARGET_ENV를 인수로 전달)
                    def healthCheckResult = sh(
                        script: "${WORKSPACE_PATH}/health-check.sh ${TARGET_ENV}",
                        returnStatus: true
                    )
                    
                    if (healthCheckResult != 0) {
                        error "대상 환경(${TARGET_ENV})의 헬스 체크가 실패했습니다. 트래픽 전환을 취소합니다."
                    }
                    
                    echo "헬스 체크 성공: 대상 환경(${TARGET_ENV})이 정상 작동합니다."
                }
            }
        }
        
        stage('Switch Traffic') {
            steps {
                script {
                    // 스크립트에 실행 권한 부여
                    sh "chmod +x ${WORKSPACE_PATH}/switch-script.sh"
                    
                    // 트래픽 전환 스크립트 실행 (인수 없이)
                    def switchResult = sh(
                        script: "export WORKSPACE=${WORKSPACE_PATH} && ${WORKSPACE_PATH}/switch-script.sh",
                        returnStatus: true
                    )
                    
                    if (switchResult != 0) {
                        error "트래픽 전환 중 오류가 발생했습니다. 롤백을 시작합니다."
                    }
                    
                    // 트래픽 전환 후 5분간 모니터링
                    echo "트래픽 전환 완료. 5분간 모니터링 중..."
                    sleep 300
                    
                    // 모니터링 후 헬스 체크 다시 실행
                    def finalHealthCheckResult = sh(
                        script: "${WORKSPACE_PATH}/health-check.sh ${TARGET_ENV}",
                        returnStatus: true
                    )
                    
                    if (finalHealthCheckResult != 0) {
                        error "전환 후 모니터링 중 문제가 발견되었습니다. 롤백을 시작합니다."
                    }
                    
                    echo "모니터링 성공: 새 환경(${TARGET_ENV})이 정상 운영 중입니다."
                    DEPLOYMENT_SUCCESS = true
                }
            }
        }

        stage('Update MR Status') {
            steps {
                updateGitlabCommitStatus name: 'build', state: 'success'

                addGitLabMRComment comment: "📦 배포 완료: ${env.BUILD_URL}\n- 환경: ${TARGET_ENV}\n- 빌드 번호: ${BUILD_VERSION}"
            }
        }
    }
    
    post {
        success {
            echo "배포 성공: ${TARGET_ENV} 환경으로 전환 완료"
            updateGitlabCommitStatus name: 'build', state: 'success'
        }

        failure {
            echo "배포 실패: 문제 발생"
            updateGitlabCommitStatus name: 'build', state: 'failed'

            script {
                // 배포 중 실패했을 경우
                if (TARGET_ENV && !DEPLOYMENT_SUCCESS) {
                    echo "새로 배포된 ${TARGET_ENV} 환경에 문제가 발생했습니다. 롤백을 시작합니다."
                    
                    // 어느 단계에서 실패했는지 확인
                    if (sh(script: "docker ps | grep -q 'omypic-${TARGET_ENV}-backend'", returnStatus: true) == 0) {
                        // 새 환경이 실행 중이면 중지
                        sh "docker compose -p omypic -f ${WORKSPACE_PATH}/docker-compose-${TARGET_ENV}.yml down"
                        echo "${TARGET_ENV} 환경을 중지했습니다."
                        
                        // 트래픽 전환이 있었는지 확인
                        def currentActive = sh(
                            script: "grep -q 'server omypic-${TARGET_ENV}-backend:8000;' ${NGINX_CONF_PATH}/upstream.conf && echo 'true' || echo 'false'",
                            returnStdout: true
                        ).trim()
                        
                        if (currentActive == "true") {
                            // 트래픽을 이전 환경으로 롤백
                            echo "트래픽을 ${CURRENT_ENV} 환경으로 롤백합니다."
                            
                            // upstream.conf 파일 롤백
                            sh """
                            cat > ${NGINX_CONF_PATH}/upstream.conf << EOF
upstream backend {
    server omypic-${CURRENT_ENV}-backend:8000;  # active
}
EOF
                            """
                            
                            // 프론트엔드 심볼릭 링크 롤백
                            sh "docker exec omypic-nginx sh -c 'ln -sfn /usr/share/nginx/${CURRENT_ENV} /usr/share/nginx/current'"
                            
                            // Nginx 설정 리로드
                            sh "docker exec omypic-nginx nginx -s reload"
                            echo "Nginx 설정 리로드 완료. 트래픽이 ${CURRENT_ENV} 환경으로 롤백되었습니다."
                        } else {
                            echo "트래픽 전환 전에 실패했습니다. 롤백이 필요하지 않습니다."
                        }
                    } else {
                        echo "새 환경 컨테이너가 실행되지 않았습니다. 롤백이 필요하지 않습니다."
                    }
                }

                addGitLabMRComment comment: "❌ 배포 실패: ${env.BUILD_URL}\n원인을 확인하세요."
            }
        }
        always {
            // 불필요한 리소스 정리
            sh 'docker system prune -f'
        }
    }
}