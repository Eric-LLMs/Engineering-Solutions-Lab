#!groovy

withFolderProperties {
    deployServiceFromGit(env.git, env.cluster, [
        preprocessFunc: {
            sh "make -C interfaces"
        },
        agentLabel: 'acme'
    ])
}
