#!groovy
// 安装supervisor

pipeline {
    agent none
    options {
        disableConcurrentBuilds()
        skipDefaultCheckout()
        timeout(time: 24, unit: 'HOURS')
        timestamps()
    }
    parameters {
        string name: 'hosts', defaultValue: '', trim: true, description: '服务器地址，逗号分隔'
        choice name: 'agent', choices: [ 'intranet', 'acme' ], description: 'jenkins slave agent'
        string name: 'ita', defaultValue: 'master', description: 'ita 自动运维模块 git revision'
        choice name: 'mode', choices: [ 'run', 'refresh' ], description: 'run - 执行任务；refresh - 刷新 jenkins 任务脚本'
        booleanParam name: 'cleanWs', defaultValue: false, description: '任务执行前，清空整个任务 workspace'
    }
    stages {
        stage('初始化') { // checkout from git
            agent { label 'intranet' }
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    if (params.cleanWs) {
                        cleanWs()
                    }

                    dir('ita') {
                        checkoutIta(params.ita)
                    }

                    if (params.agent != 'intranet') {
                        stash includes: 'ita/', name: 'ita'
                    }
                }
            }
            post {
                always {
                    script {
                        setBuildDesc("hosts = ${params.hosts}\nita = ${params.ita}\nmode = ${params.mode}")
                    }
                }
            }
        }
        stage('执行') {
            agent { label params.agent }
            when {
                allOf {
                    expression { return params.mode != 'refresh' }
                    expression { return params.hosts != '' }
                }
            }
            steps {
                script {
                    if (params.agent != 'intranet') {
                        unstash 'ita'
                    }

                    dir('ita') {
                        sh "ansible-playbook playbooks/common-server/install-supervisord.yml -e servers=${params.hosts}"
                    }
                }
			}
        }
    }
}
