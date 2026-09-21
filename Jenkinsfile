pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Select whether to deploy a new version or rollback'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['UAT', 'PRODUCTION'],
            description: 'Select the deployment environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Enter the application version to deploy'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['YES', 'NO'],
            description: 'Production deployment requires explicit confirmation'
        )
    }

    stages {

        stage('Show Parameters') {
            steps {
                echo "======================================"
                echo "DEPLOYMENT_ACTION = ${params.DEPLOYMENT_ACTION}"
                echo "ENVIRONMENT       = ${params.ENVIRONMENT}"
                echo "VERSION           = ${params.VERSION}"
                echo "CONFIRM_PROD      = ${params.CONFIRM_PROD}"
                echo "======================================"
            }
        }

        stage('Production Confirmation') {
            steps {
                script {
                    if (params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES') {

                        error("Production deployment blocked: CONFIRM_PROD must be YES.")
                    }

                    echo "Environment confirmation passed."
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate Git Version') {
            steps {
                bat """
                    echo Checking Git tag for version ${params.VERSION}
                    git fetch --tags origin
                    git rev-parse --verify refs/tags/v${params.VERSION}
                    git checkout tags/v${params.VERSION}
                """
            }
        }

        stage('Identify Git Commit') {
            steps {
                script {
                    def commit = bat(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Selected Git commit: ${commit}"
                }
            }
        }
    }
}