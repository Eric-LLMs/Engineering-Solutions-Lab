#!groovy
// 部署prometheus

pipeline {
    agent none
    options {
        disableConcurrentBuilds()
        skipDefaultCheckout()
        timeout(time: 24, unit: 'HOURS')
        timestamps()
    }
    stages {
        stage('初始化') { // checkout from git
            agent { label 'intranet' }
            steps {
                script {
                    dir('ita') {
                        checkoutIta()
                    }

                    stash includes: 'ita/', name: 'ita'
                }
            }
        }
        stage('部署内网') {
            agent { label 'intranet' }
            steps {
                script {
                    dir('ita') {
                        sh "ansible-playbook playbooks/prometheus/deploy.yml -e cluster=intranet"
                    }
                }
            }
        }
        stage('部署 acme') {
            agent { label 'acme' }
            steps {
                script {
                    unstash 'ita'

                    dir('ita') {
                        sh "ansible-playbook playbooks/prometheus/deploy.yml -e cluster=acme"
                    }
                }
            }
        }
    }
}
