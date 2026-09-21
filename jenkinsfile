pipeline {
    agent any

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

    }
}