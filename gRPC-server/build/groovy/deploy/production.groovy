#!groovy

withFolderProperties {
    deployServiceFromGit(env.git, env.cluster, [
        serial: '1',
        preprocessFunc: {
            sh "make -C interfaces"
        },
        needApproval: true,
        agentLabel: 'acme'
    ])
}
