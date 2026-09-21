pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

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
            description: 'Enter the application version to deploy or validate'
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
                echo "DEPLOYMENT ACTION : ${params.DEPLOYMENT_ACTION}"
                echo "ENVIRONMENT       : ${params.ENVIRONMENT}"
                echo "VERSION           : ${params.VERSION}"
                echo "CONFIRM PROD      : ${params.CONFIRM_PROD}"
                echo "======================================"
            }
        }

        stage('Production Confirmation') {
            steps {
                script {

                    if (params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES') {

                        error(
                            "Production deployment blocked: CONFIRM_PROD must be YES."
                        )
                    }

                    echo "Environment confirmation passed."
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm

                bat """
                    echo Fetching Git tags...
                    git fetch --tags origin

                    echo Checking out requested version...
                    git checkout tags/v${params.VERSION}
                """
            }
        }

        stage('Validate Git Version') {
            steps {
                bat """
                    echo ======================================
                    echo Validating version v${params.VERSION}
                    echo ======================================

                    git rev-parse --verify refs/tags/v${params.VERSION}

                    echo Version v${params.VERSION} exists.
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

                    echo "======================================"
                    echo "Selected Git commit:"
                    echo "${commit}"
                    echo "======================================"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {

                    echo "======================================"
                    echo "Building Docker image"
                    echo "Image: retail-app:${params.VERSION}"
                    echo "======================================"

                    bat """
                        docker build -t retail-app:${params.VERSION} .
                    """

                    echo "Docker image built successfully."
                }
            }
        }

        stage('Verify Docker Image') {
            steps {
                bat """
                    echo ======================================
                    echo Docker image verification
                    echo ======================================

                    docker image inspect retail-app:${params.VERSION}

                    echo Docker image retail-app:${params.VERSION} exists.
                """
            }
        }
    }

    post {

        success {
            echo "======================================"
            echo "PIPELINE STATUS: SUCCESS"
            echo "Version: ${params.VERSION}"
            echo "Action: ${params.DEPLOYMENT_ACTION}"
            echo "Environment: ${params.ENVIRONMENT}"
            echo "======================================"
        }

        failure {
            echo "======================================"
            echo "PIPELINE STATUS: FAILURE"
            echo "Check the console output above."
            echo "======================================"
        }
    }
}