#!groovy

@Library('shared-lib') _

regressionTest('git@192.168.1.78:model-services/http-proxy.git', 'build/playbooks/regression.yml')
