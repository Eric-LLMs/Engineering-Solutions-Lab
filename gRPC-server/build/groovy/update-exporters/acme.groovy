#!groovy

withFolderProperties {
    updateExporters(env.git, env.cluster, [
        agentLabel: 'acme'
    ])
}
