#!groovy
// 质量分析

pipeline {
    agent { label 'intranet' }
    options {
		disableConcurrentBuilds()
		skipDefaultCheckout()
		timeout(time: 24, unit: 'HOURS')
		timestamps()
    }
    parameters {
        string name: 'revision', defaultValue: 'master', trim: true, description: '需要部署的模块 git revision/branch/tag 版本'
        choice name: 'mode', choices: [ 'normal', 'refresh' ], description: '任务模式：normal - 执行任务；refresh - 刷新 jenkins 任务脚本'
        booleanParam name: 'cleanWs', defaultValue: false, description: '任务执行前，清空整个任务 workspace'
        booleanParam name: 'silent', defaultValue: false, description: '静默 jenkins 报警'
        // cluster
        // type
    }
    stages {
        stage('初始化') { // checkout from git
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    if (params.cleanWs) {
                        cleanWs()
                    }

                    // 拉取建库项目
                    dir('code') {
                        checkoutGit('git@192.168.1.78:searchers/quality-analysis.git', params.revision)
                    }
				}
            }
            post {
                always {
                    script {
                        dir('code') {
                            // 设置构建信息
                            shortCommit = getGitShortCommit()
                            setBuildDesc("revision = ${params.revision}(${shortCommit})")
                        }
                    }
                }
            }
        }
        stage('预处理') {
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    dir('code') {
                        sh "pip3 install -r requirements.txt -i https://mirrors.acme.com/pypi/simple/"
                    }
                }
            }
            post {
                failure {
                    // 钉钉报告异常
                    script {
                        if (!params.silent) {
                            sendErrorMdDingMsg("建库预处理失败！")
                        }
                    }
                }
            }
        }
        stage('质量分析') {
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    dir('code') {
                        sh "python3 main.py --conf config/${params.cluster}.yml --type ${params.type}"
                    }
                }
            }
            post {
                failure {
                    // 钉钉报告异常
                    script {
                        if (!params.silent) {
                            sendErrorMdDingMsg("质量分析失败！")
                        }
                    }
                }
            }
		}
    }
}
