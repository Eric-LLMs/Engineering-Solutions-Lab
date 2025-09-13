#!groovy

withFolderProperties {
    regressionTest(env.git, env.cluster)
}
