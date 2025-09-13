#!groovy

withFolderProperties {
    updateExporters(env.git, env.cluster)
}
