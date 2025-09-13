#!groovy

withFolderProperties {
    runCommand(env.git, env.cluster, 'playbooks/restart.yml', [
        agentLabel: 'acme'
    ])
}
