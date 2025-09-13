#!groovy

withFolderProperties {
    runCommand(env.git, env.cluster, 'playbooks/restart.yml', [
        serial: '1',
        agentLabel: 'acme'
    ])
}
