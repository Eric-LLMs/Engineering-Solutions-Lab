#!groovy
// 镜像构建

pipeline {
    agent none
    options {
		disableConcurrentBuilds()
		skipDefaultCheckout()
		timeout(time: 2, unit: 'HOURS')
		timestamps()
    }
    parameters {
        choice name: 'agent', choices: [ 'intranet', 'acme' ], description: 'jenkins slave agent'
        string name: 'ita', defaultValue: 'master', description: 'ita 自动运维模块 git revision'
        choice name: 'mode', choices: [ 'run', 'refresh' ], description: 'run - 执行任务；refresh - 刷新 jenkins 任务脚本'
        booleanParam name: 'cleanWs', defaultValue: false, description: '任务执行前，清空整个任务 workspace'
        // name
        // tag
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
                        setBuildDesc("agent = ${params.agent}\nname = ${params.name}\ntag = ${params.tag}\nita = ${params.ita}")
                    }
                }
            }
        }
        stage('docker 构建') { // build
            agent { label params.agent }
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    if (params.agent != 'intranet') {
                        unstash 'ita'
                    }

                    dir('ita') {
                        sh "ansible-playbook playbooks/docker/build.yml -e image_name=${params.name} -e image_ver=${params.tag} -e cluster=docker_builder_${params.agent}"
                    }
                }
            }
        }
    }
}
