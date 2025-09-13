#!groovy
// 更新知识图谱

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
        booleanParam name: 'publish', defaultValue: true, description: '建库数据是否发布到服务'
        booleanParam name: 'cleanWs', defaultValue: false, description: '任务执行前，清空整个任务 workspace'
        booleanParam name: 'silent', defaultValue: false, description: '静默 jenkins 报警'
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

                    withFolderProperties {
                        cluster = env.cluster
                    }

                    // 拉取建库项目
                    dir('code') {
                        checkoutGit('git@192.168.1.78:searchers/data-trigger.git', params.revision)
                    }
                    dir('ita') {
                        checkoutIta()
                    }
				}
            }
            post {
                always {
                    script {
                        dir('code') {
                            // 设置构建信息
                            shortCommit = getGitShortCommit()
                            setBuildDesc("revision = ${params.revision}(${shortCommit})\ntype = ${params.type}")
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
        stage('数据生成') {
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    dir('code') {
                        withFolderProperties {
                            sh "python3 taskflow.py --conf conf/knowledge_graph/${params.type}-${cluster}.yml"
                        }
                    }
                }
            }
            post {
                failure {
                    // 钉钉报告异常
                    script {
                        if (!params.silent) {
                            sendErrorMdDingMsg("数据生成失败！")
                        }
                    }
                }
            }
		}
        stage('发布') {
            when {
                expression { return params.mode != 'refresh' }
            }
            steps {
                script {
                    dir("ita") {
                        sh "ansible-playbook playbooks/data-center/push-direct.yml -e data_source=\"\$(pwd)/../code/output/kg/${params.type}\" -e data_dest=\"${cluster}/dict-service/dict/latest/kg/${params.type}\" -e datacenter=datacenter_intranet -e delete_excluded=1"

                        if (params.publish) {
                            // 推送到指定集群
                            sh """
                                ansible-playbook playbooks/services/push-direct.yml -e data_source="\$(pwd)/../code/output/kg/${params.type}" -e data_dest="{{ deploy_path }}/dict/kg/${params.type}" -e cluster=dict_service_${cluster} -e serial_list=8 -e delete_excluded=1
                                """

                            // 更新命令
                            build job: "Algorithm/Algorithm-v2/dict-service/${cluster}/run-command", parameters: [string(name: 'argus', value: 'bin/ds_control reload -l 1'), string(name: 'mode', value: 'normal'), booleanParam(name: 'cleanWs', value: params.cleanWs), booleanParam(name: 'silent', value: params.silent)], quietPeriod: 1
                        }
                    }
                }
            }
        }
    }
}
