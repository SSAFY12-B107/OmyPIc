pipeline {
    agent any
    stages {
        stage('Git Clone') {
            steps {
                git branch : 'dev', credentialsId :'gitlab-user-pwd', url: 'https://lab.ssafy.com/s12-ai-speech-sub1/S12P21B107.git'
            }
            post {
                failure {
                    echo 'Repository clone failure !'
                }
                success {
                    echo 'Repository clone success !'
                }
            }
        }
    }
}