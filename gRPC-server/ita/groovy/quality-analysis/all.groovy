#!groovy
// 全类目建库

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
    }
    stages {
        stage('准备') {
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    setBuildDesc("revision = ${params.revision}\ncluster = ${params.cluster}\ncleanIdx = ${params.cleanIdx}")
                }
            }
        }
        stage('并行建库') {
            parallel {
                stage('会议') {
                    when {
                        expression { return params.mode != 'refresh' }
                    }
                    steps {
                        script {
                            downstream = build job: "conference/${params.cluster}", quietPeriod: 1, propagate: false, parameters: [string(name: 'revision', value: params.revision), string(name: 'mode', value: params.mode), string(name: 'cluster', value: params.cluster), booleanParam(name: 'cleanWs', value: params.cleanWs), booleanParam(name: 'silent', value: params.silent)]
                        }
                    }
                    post {
                        always {
                            script {
                                if (downstream.result == 'FAILURE') {
                                    currentBuild.result = 'UNSTABLE'
                                }
                            }
                        }
                    }
                }
                stage('医师') {
                    when {
                        expression { return params.mode != 'refresh' }
                    }
                    steps {
                        script {
                            downstream = build job: "customer/${params.cluster}", quietPeriod: 1, propagate: false, parameters: [string(name: 'revision', value: params.revision), string(name: 'mode', value: params.mode), string(name: 'cluster', value: params.cluster), booleanParam(name: 'cleanWs', value: params.cleanWs), booleanParam(name: 'silent', value: params.silent)]
                        }
                    }
                    post {
                        always {
                            script {
                                if (downstream.result == 'FAILURE') {
                                    currentBuild.result = 'UNSTABLE'
                                }
                            }
                        }
                    }
                }
                stage('文库') {
                    when {
                        expression { return params.mode != 'refresh' }
                    }
                    steps {
                        script {
                            downstream = build job: "doc/${params.cluster}", quietPeriod: 1, propagate: false, parameters: [string(name: 'revision', value: params.revision), string(name: 'mode', value: params.mode), string(name: 'cluster', value: params.cluster), booleanParam(name: 'cleanWs', value: params.cleanWs), booleanParam(name: 'silent', value: params.silent)]
                        }
                    }
                    post {
                        always {
                            script {
                                if (downstream.result == 'FAILURE') {
                                    currentBuild.result = 'UNSTABLE'
                                }
                            }
                        }
                    }
                }
                stage('病例') {
                    when {
                        expression { return params.mode != 'refresh' }
                    }
                    steps {
                        script {
                            downstream = build job: "case/${params.cluster}", quietPeriod: 1, propagate: false, parameters: [string(name: 'revision', value: params.revision), string(name: 'mode', value: params.mode), string(name: 'cluster', value: params.cluster), booleanParam(name: 'cleanWs', value: params.cleanWs), booleanParam(name: 'silent', value: params.silent)]
                        }
                    }
                    post {
                        always {
                            script {
                                if (downstream.result == 'FAILURE') {
                                    currentBuild.result = 'UNSTABLE'
                                }
                            }
                        }
                    }
                }
                stage('视频') {
                    when {
                        expression { return params.mode != 'refresh' }
                    }
                    steps {
                        script {
                            downstream = build job: "video/${params.cluster}", quietPeriod: 1, propagate: false, parameters: [string(name: 'revision', value: params.revision), string(name: 'mode', value: params.mode), string(name: 'cluster', value: params.cluster), booleanParam(name: 'cleanWs', value: params.cleanWs), booleanParam(name: 'silent', value: params.silent)]
                        }
                    }
                    post {
                        always {
                            script {
                                if (downstream.result == 'FAILURE') {
                                    currentBuild.result = 'UNSTABLE'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
