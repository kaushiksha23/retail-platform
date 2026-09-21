pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
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

        stage('Validate Parameters') {
            steps {
                script {

                    if (!(params.VERSION ==~ /^[0-9]+\.[0-9]+\.[0-9]+$/)) {
                        error("Invalid VERSION. Use format like 4.2.1")
                    }

                    if (params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES') {

                        error(
                            "Production deployment blocked: CONFIRM_PROD must be YES."
                        )
                    }

                    echo "Parameter validation passed."
                }
            }
        }

        stage('Checkout Requested Version') {
            steps {
                checkout scm

                bat """
                    echo ======================================
                    echo Fetching Git tags
                    echo ======================================

                    git fetch --tags origin

                    echo Checking out requested version v${params.VERSION}

                    git checkout tags/v${params.VERSION}
                """
            }
        }

        stage('Validate Git Version') {
            steps {
                bat """
                    echo ======================================
                    echo Validating Git tag
                    echo ======================================

                    git rev-parse --verify refs/tags/v${params.VERSION}

                    echo Git tag v${params.VERSION} exists.
                """
            }
        }

        stage('Identify Git Commit') {
            steps {
                script {

                    def commit = bat(
                        script: '@git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    echo "======================================"
                    echo "DEPLOYMENT TRACEABILITY"
                    echo "Version : v${params.VERSION}"
                    echo "Commit  : ${commit}"
                    echo "======================================"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "======================================"
                echo "Building Docker image"
                echo "Image: retail-app:${params.VERSION}"
                echo "======================================"

                bat """
                    docker build -t retail-app:${params.VERSION} .
                """
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

        stage('Deploy / Rollback') {
            steps {
                script {

                    /*
                     * Make sure the Docker network exists.
                     */
                    bat """
                        docker network inspect retail-network >NUL 2>&1 || docker network create retail-network
                    """

                    /*
                     * Find the currently running container using host port 8081.
                     */
                    def previousContainer = bat(
                        script: '@docker ps --filter "publish=8081" --format "{{.Names}}"',
                        returnStdout: true
                    ).trim()

                    env.PREVIOUS_CONTAINER = previousContainer

                    echo "======================================"
                    echo "CURRENT PRODUCTION STATE"
                    echo "Previous container: ${previousContainer ?: 'NONE'}"
                    echo "======================================"

                    /*
                     * DEPLOY
                     */
                    if (params.DEPLOYMENT_ACTION == 'DEPLOY') {

                        def previousImage = ""

                        if (previousContainer) {

                            previousImage = bat(
                                script: "@docker inspect -f \"{{.Config.Image}}\" ${previousContainer}",
                                returnStdout: true
                            ).trim()

                            env.PREVIOUS_IMAGE = previousImage

                            echo "Previous image: ${previousImage}"

                            /*
                             * Save the previous image under a stable rollback tag.
                             */
                            bat """
                                docker tag ${previousImage} retail-app:previous
                            """

                            echo "Previous image saved as retail-app:previous."
                        }
                        else {
                            echo "No previous container found."
                        }

                        /*
                         * Remove any leftover candidate container.
                         */
                        bat """
                            docker rm -f retail-platform-candidate >NUL 2>&1 || exit /b 0
                        """

                        /*
                         * Start candidate on temporary port 18081.
                         *
                         * IMPORTANT:
                         * The old application on 8081 is still running.
                         * We only replace it after the candidate becomes healthy.
                         */
                        echo "======================================"
                        echo "STARTING CANDIDATE"
                        echo "Image: retail-app:${params.VERSION}"
                        echo "Port : 18081"
                        echo "======================================"

                        bat """
                            docker run -d ^
                              --name retail-platform-candidate ^
                              --network retail-network ^
                              -p 18081:8081 ^
                              -e APP_VERSION=${params.VERSION} ^
                              -e FORCE_HEALTH_FAIL=false ^
                              retail-app:${params.VERSION}
                        """

                        /*
                         * Wait for Docker HEALTHCHECK.
                         */
                        echo "Waiting for candidate health check..."

                        def candidateHealthy = false

                        for (int i = 0; i < 15; i++) {

                            def health = bat(
                                script: '@docker inspect -f "{{.State.Health.Status}}" retail-platform-candidate',
                                returnStdout: true
                            ).trim()

                            echo "Candidate health: ${health}"

                            if (health == 'healthy') {
                                candidateHealthy = true
                                break
                            }

                            if (health == 'unhealthy') {
                                break
                            }

                            sleep(time: 2, unit: 'SECONDS')
                        }

                        /*
                         * Candidate failed.
                         * Old production container is still untouched.
                         */
                        if (!candidateHealthy) {

                            echo "======================================"
                            echo "CANDIDATE HEALTH CHECK FAILED"
                            echo "Old production container was NOT removed."
                            echo "Cleaning candidate..."
                            echo "======================================"

                            bat """
                                docker logs retail-platform-candidate
                                docker rm -f retail-platform-candidate
                            """

                            error(
                                "Deployment stopped because candidate version failed health check."
                            )
                        }

                        /*
                         * Candidate is healthy.
                         * Now perform the production swap.
                         */
                        echo "======================================"
                        echo "CANDIDATE HEALTHY"
                        echo "Starting production swap..."
                        echo "======================================"

                        if (previousContainer) {

                            echo "Stopping previous container: ${previousContainer}"

                            bat """
                                docker stop ${previousContainer}
                                docker rm ${previousContainer}
                            """
                        }

                        /*
                         * Start the new production container.
                         */
                        bat """
                            docker run -d ^
                              --name retail-platform-app ^
                              --network retail-network ^
                              -p 8081:8081 ^
                              -e APP_VERSION=${params.VERSION} ^
                              -e FORCE_HEALTH_FAIL=false ^
                              retail-app:${params.VERSION}
                        """

                        /*
                         * Candidate is no longer required.
                         */
                        bat """
                            docker rm -f retail-platform-candidate
                        """

                        /*
                         * Verify production health.
                         */
                        echo "======================================"
                        echo "VERIFYING PRODUCTION"
                        echo "======================================"

                        def productionHealthy = false

                        for (int i = 0; i < 15; i++) {

                            def health = bat(
                                script: '@docker inspect -f "{{.State.Health.Status}}" retail-platform-app',
                                returnStdout: true
                            ).trim()

                            echo "Production health: ${health}"

                            if (health == 'healthy') {
                                productionHealthy = true
                                break
                            }

                            if (health == 'unhealthy') {
                                break
                            }

                            sleep(time: 2, unit: 'SECONDS')
                        }

                        /*
                         * Production health failed AFTER swap.
                         * Roll back automatically.
                         */
                        if (!productionHealthy) {

                            echo "======================================"
                            echo "PRODUCTION HEALTH CHECK FAILED"
                            echo "STARTING AUTOMATIC ROLLBACK"
                            echo "======================================"

                            bat """
                                docker logs retail-platform-app
                                docker stop retail-platform-app
                                docker rm retail-platform-app
                            """

                            if (previousImage) {

                                echo "Restoring previous image: ${previousImage}"

                                bat """
                                    docker run -d ^
                                      --name retail-platform-app ^
                                      --network retail-network ^
                                      -p 8081:8081 ^
                                      -e FORCE_HEALTH_FAIL=false ^
                                      ${previousImage}
                                """

                                sleep(time: 3, unit: 'SECONDS')

                                def rollbackHealth = bat(
                                    script: '@docker inspect -f "{{.State.Health.Status}}" retail-platform-app',
                                    returnStdout: true
                                ).trim()

                                echo "Rollback health: ${rollbackHealth}"

                                if (rollbackHealth != 'healthy') {
                                    error(
                                        "CRITICAL: rollback container did not become healthy."
                                    )
                                }

                                echo "======================================"
                                echo "ROLLBACK VERIFIED"
                                echo "Restored image: ${previousImage}"
                                echo "======================================"

                            } else {

                                error(
                                    "Production deployment failed and no previous image was available for rollback."
                                )
                            }

                            /*
                             * IMPORTANT:
                             * The deployment must be marked FAILURE because
                             * rollback was required.
                             */
                            error(
                                "DEPLOYMENT FAILED: health check failed. Previous version was restored successfully."
                            )
                        }

                        echo "======================================"
                        echo "DEPLOYMENT SUCCESSFUL"
                        echo "New image: retail-app:${params.VERSION}"
                        echo "Production health: HEALTHY"
                        echo "======================================"
                    }

                    /*
                     * ROLLBACK
                     */
                    else {

                        echo "======================================"
                        echo "ROLLBACK REQUESTED"
                        echo "======================================"

                        def rollbackImage = bat(
                            script: '@docker image inspect retail-app:previous --format "{{.RepoTags}}"',
                            returnStdout: true
                        ).trim()

                        if (!rollbackImage) {
                            error(
                                "Rollback image retail-app:previous does not exist."
                            )
                        }

                        echo "Rollback image available: retail-app:previous"

                        /*
                         * Remove current application.
                         */
                        bat """
                            docker rm -f retail-platform-app >NUL 2>&1 || exit /b 0
                        """

                        /*
                         * Start previous version.
                         */
                        bat """
                            docker run -d ^
                              --name retail-platform-app ^
                              --network retail-network ^
                              -p 8081:8081 ^
                              -e FORCE_HEALTH_FAIL=false ^
                              retail-app:previous
                        """

                        sleep(time: 3, unit: 'SECONDS')

                        def rollbackHealthy = false

                        for (int i = 0; i < 15; i++) {

                            def health = bat(
                                script: '@docker inspect -f "{{.State.Health.Status}}" retail-platform-app',
                                returnStdout: true
                            ).trim()

                            echo "Rollback health: ${health}"

                            if (health == 'healthy') {
                                rollbackHealthy = true
                                break
                            }

                            sleep(time: 2, unit: 'SECONDS')
                        }

                        if (!rollbackHealthy) {
                            error(
                                "Rollback failed: previous version is not healthy."
                            )
                        }

                        echo "======================================"
                        echo "ROLLBACK SUCCESSFUL"
                        echo "Image: retail-app:previous"
                        echo "Health: HEALTHY"
                        echo "======================================"
                    }
                }
            }
        }

        stage('Deployment Validation') {
            steps {
                bat """
                    echo ======================================
                    echo FINAL DEPLOYMENT VALIDATION
                    echo ======================================

                    docker ps

                    echo.
                    echo Checking application health endpoint...

                    curl -f http://127.0.0.1:8081/health

                    echo.
                    echo ======================================
                    echo APPLICATION HEALTH CHECK PASSED
                    echo ======================================
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
            echo "Deployment failed or rollback was required."
            echo "Check the console output for old/new/final state."
            echo "======================================"
        }

        always {
            echo "======================================"
            echo "PIPELINE COMPLETED"
            echo "======================================"
        }
    }
}