#!groovy

@Library('shared-lib') _

deployServiceFromGit('git@192.168.1.78:model-services/http-proxy.git', 'build/playbooks/deploy.yml', [
    preprocessFunc: {
        sh "make -C app/interfaces"
    },
    agentLabel: 'acme'
])
