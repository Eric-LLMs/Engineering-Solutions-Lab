#!groovy

@Library('shared-lib') _

updateExporters('git@192.168.1.78:model-services/http-proxy.git', 'build/playbooks/update-exporters.yml', [
    agentLabel: 'acme'
])
