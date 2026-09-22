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
            defaultValue: '4.2.3',
            description: 'Enter the application version to deploy or validate'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['YES', 'NO'],
            description: 'Production deployment requires explicit confirmation'
        )

        choice(
            name: 'FAIL_HEALTH_CHECK',
            choices: ['NO', 'YES'],
            description: 'Enable failure injection for mandatory rollback demonstration'
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
                echo "FAIL HEALTH CHECK : ${params.FAIL_HEALTH_CHECK}"
                echo "======================================"
            }
        }


        stage('Validate Parameters') {

            steps {

                script {

                    if (!(params.VERSION ==~ /^[0-9]+\.[0-9]+\.[0-9]+$/)) {

                        error(
                            "Invalid VERSION. Use format like 4.2.3"
                        )
                    }


                    if (
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES'
                    ) {

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
                echo "BUILDING DOCKER IMAGE"
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

                    echo.
                    echo Docker image retail-app:${params.VERSION} exists.

                """
            }
        }


        stage('Deploy / Rollback') {

            steps {

                script {


                    /*
                     * Make sure deployment network exists.
                     */

                    bat """

                        docker network inspect retail-network >NUL 2>&1 || docker network create retail-network

                    """


                    /*
                     * Find the currently running application
                     * using host port 8081.
                     */

                    def previousContainer = bat(
                        script: '@docker ps --filter "publish=8081" --format "{{.Names}}"',
                        returnStdout: true
                    ).trim()


                    /*
                     * If multiple names are returned,
                     * use the first one.
                     */

                    if (previousContainer) {

                        previousContainer =
                            previousContainer.readLines()[0].trim()
                    }


                    echo "======================================"
                    echo "CURRENT DEPLOYMENT STATE"
                    echo "Previous container: ${previousContainer ?: 'NONE'}"
                    echo "======================================"


                    /*
                     * ==================================================
                     * DEPLOY
                     * ==================================================
                     */

                    if (params.DEPLOYMENT_ACTION == 'DEPLOY') {


                        def previousImage = ""


                        /*
                         * Save previous production image.
                         */

                        if (previousContainer) {

                            previousImage = bat(
                                script: "@docker inspect -f \"{{.Config.Image}}\" ${previousContainer}",
                                returnStdout: true
                            ).trim()


                            echo "Previous image: ${previousImage}"


                            /*
                             * Save stable rollback tag.
                             */

                            bat """

                                docker tag ${previousImage} retail-app:previous

                            """


                            echo "Previous image saved as retail-app:previous."
                        }
                        else {

                            echo "No previous production container found."
                        }


                        /*
                         * Remove stale candidate if one exists.
                         */

                        bat """

                            docker rm -f retail-platform-candidate >NUL 2>&1 || exit /b 0

                        """


                        /*
                         * ==================================================
                         * CANDIDATE DEPLOYMENT
                         *
                         * Candidate ALWAYS starts with health failure
                         * disabled.
                         *
                         * This verifies that the new image itself is valid
                         * before production replacement.
                         * ==================================================
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
                         * Verify candidate has a Docker HEALTHCHECK.
                         */

                        echo "Checking candidate healthcheck configuration..."


                        def hasHealthCheck = bat(
                            script: '@docker inspect -f "{{if .Config.Healthcheck}}YES{{else}}NO{{end}}" retail-platform-candidate',
                            returnStdout: true
                        ).trim()


                        echo "Candidate HEALTHCHECK configured: ${hasHealthCheck}"


                        if (hasHealthCheck != 'YES') {

                            bat """

                                docker logs retail-platform-candidate

                                docker rm -f retail-platform-candidate

                            """


                            error(
                                "Deployment stopped: candidate image does not contain a Docker HEALTHCHECK."
                            )
                        }


                        /*
                         * Wait for candidate to become healthy.
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


                            sleep(
                                time: 2,
                                unit: 'SECONDS'
                            )
                        }


                        /*
                         * Candidate failed before production swap.
                         */

                        if (!candidateHealthy) {


                            echo "======================================"
                            echo "CANDIDATE HEALTH CHECK FAILED"
                            echo "PRODUCTION WAS NOT TOUCHED"
                            echo "======================================"


                            bat """

                                docker logs retail-platform-candidate

                                docker rm -f retail-platform-candidate

                            """


                            error(
                                "Deployment stopped because candidate failed health check."
                            )
                        }


                        echo "======================================"
                        echo "CANDIDATE HEALTHY"
                        echo "Candidate version is ready."
                        echo "======================================"


                        /*
                         * ==================================================
                         * PRODUCTION SWAP
                         *
                         * Old version is removed only after the new
                         * candidate has passed its health check.
                         * ==================================================
                         */

                        if (previousContainer) {

                            echo "Stopping previous container: ${previousContainer}"


                            bat """

                                docker stop ${previousContainer}

                                docker rm ${previousContainer}

                            """
                        }


                        /*
                         * Determine whether failure injection is enabled.
                         */

                        def healthFailValue = 'false'


                        if (params.FAIL_HEALTH_CHECK == 'YES') {

                            healthFailValue = 'true'


                            echo "======================================"
                            echo "FAILURE INJECTION ENABLED"
                            echo "FORCE_HEALTH_FAIL=true"
                            echo "Production health check WILL FAIL"
                            echo "Automatic rollback will be tested."
                            echo "======================================"
                        }
                        else {

                            echo "Failure injection disabled."
                        }


                        /*
                         * Start new production version.
                         */

                        bat """

                            docker run -d ^
                              --name retail-platform-app ^
                              --network retail-network ^
                              -p 8081:8081 ^
                              -e APP_VERSION=${params.VERSION} ^
                              -e FORCE_HEALTH_FAIL=${healthFailValue} ^
                              retail-app:${params.VERSION}

                        """


                        /*
                         * Candidate no longer needed.
                         */

                        bat """

                            docker rm -f retail-platform-candidate >NUL 2>&1 || exit /b 0

                        """


                        /*
                         * ==================================================
                         * PRODUCTION HEALTH CHECK
                         * ==================================================
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


                            sleep(
                                time: 2,
                                unit: 'SECONDS'
                            )
                        }


                        /*
                         * ==================================================
                         * AUTOMATIC ROLLBACK
                         * ==================================================
                         */

                        if (!productionHealthy) {


                            echo "======================================"
                            echo "PRODUCTION HEALTH CHECK FAILED"
                            echo "AUTOMATIC ROLLBACK STARTING"
                            echo "======================================"


                            /*
                             * Capture failed version logs.
                             */

                            bat """

                                docker logs retail-platform-app

                            """


                            /*
                             * Remove failed production version.
                             */

                            bat """

                                docker stop retail-platform-app

                                docker rm retail-platform-app

                            """


                            /*
                             * Restore previous image.
                             */

                            if (previousImage) {


                                echo "======================================"
                                echo "RESTORING PREVIOUS VERSION"
                                echo "Previous image: ${previousImage}"
                                echo "======================================"


                                bat """

                                    docker run -d ^
                                      --name retail-platform-app ^
                                      --network retail-network ^
                                      -p 8081:8081 ^
                                      -e FORCE_HEALTH_FAIL=false ^
                                      ${previousImage}

                                """


                                /*
                                 * Verify rollback image has HEALTHCHECK.
                                 */

                                def rollbackHasHealthCheck = bat(
                                    script: '@docker inspect -f "{{if .Config.Healthcheck}}YES{{else}}NO{{end}}" retail-platform-app',
                                    returnStdout: true
                                ).trim()


                                echo "Rollback HEALTHCHECK configured: ${rollbackHasHealthCheck}"


                                if (rollbackHasHealthCheck != 'YES') {

                                    error(
                                        "CRITICAL: rollback image does not contain a Docker HEALTHCHECK."
                                    )
                                }


                                /*
                                 * Wait for rollback health.
                                 */

                                def rollbackHealthy = false


                                for (int i = 0; i < 15; i++) {


                                    def rollbackHealth = bat(
                                        script: '@docker inspect -f "{{.State.Health.Status}}" retail-platform-app',
                                        returnStdout: true
                                    ).trim()


                                    echo "Rollback health: ${rollbackHealth}"


                                    if (rollbackHealth == 'healthy') {

                                        rollbackHealthy = true
                                        break
                                    }


                                    sleep(
                                        time: 2,
                                        unit: 'SECONDS'
                                    )
                                }


                                /*
                                 * Rollback verification.
                                 */

                                if (!rollbackHealthy) {

                                    error(
                                        "CRITICAL: rollback container did not become healthy."
                                    )
                                }


                                echo "======================================"
                                echo "ROLLBACK VERIFIED"
                                echo "Previous image restored: ${previousImage}"
                                echo "Rollback health: HEALTHY"
                                echo "======================================"


                                /*
                                 * IMPORTANT:
                                 *
                                 * Assessment requires the pipeline to show
                                 * FAILURE when rollback was required.
                                 */

                                error(
                                    "DEPLOYMENT FAILED: health check failed. Previous version was restored successfully."
                                )

                            }
                            else {

                                error(
                                    "CRITICAL: deployment failed and no previous image was available for rollback."
                                )
                            }
                        }


                        /*
                         * Successful deployment.
                         */

                        echo "======================================"
                        echo "DEPLOYMENT SUCCESSFUL"
                        echo "New image: retail-app:${params.VERSION}"
                        echo "Production health: HEALTHY"
                        echo "======================================"
                    }


                    /*
                     * ==================================================
                     * MANUAL ROLLBACK
                     * ==================================================
                     */

                    else {


                        echo "======================================"
                        echo "MANUAL ROLLBACK REQUESTED"
                        echo "======================================"


                        /*
                         * Check that rollback image exists.
                         */

                        def rollbackExists = bat(
                            script: '@docker image inspect retail-app:previous >NUL 2>&1',
                            returnStatus: true
                        )


                        if (rollbackExists != 0) {

                            error(
                                "Rollback image retail-app:previous does not exist."
                            )
                        }


                        echo "Rollback image retail-app:previous exists."


                        /*
                         * Remove current production container.
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


                        /*
                         * Verify rollback healthcheck exists.
                         */

                        def manualRollbackHealthCheck = bat(
                            script: '@docker inspect -f "{{if .Config.Healthcheck}}YES{{else}}NO{{end}}" retail-platform-app',
                            returnStdout: true
                        ).trim()


                        echo "Rollback HEALTHCHECK configured: ${manualRollbackHealthCheck}"


                        if (manualRollbackHealthCheck != 'YES') {

                            error(
                                "Rollback image does not contain a Docker HEALTHCHECK."
                            )
                        }


                        /*
                         * Wait for rollback health.
                         */

                        def manualRollbackHealthy = false


                        for (int i = 0; i < 15; i++) {


                            def health = bat(
                                script: '@docker inspect -f "{{.State.Health.Status}}" retail-platform-app',
                                returnStdout: true
                            ).trim()


                            echo "Rollback health: ${health}"


                            if (health == 'healthy') {

                                manualRollbackHealthy = true
                                break
                            }


                            sleep(
                                time: 2,
                                unit: 'SECONDS'
                            )
                        }


                        if (!manualRollbackHealthy) {

                            error(
                                "Manual rollback failed: previous version is not healthy."
                            )
                        }


                        echo "======================================"
                        echo "MANUAL ROLLBACK SUCCESSFUL"
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
            echo "Failure Injection: ${params.FAIL_HEALTH_CHECK}"
            echo "======================================"
        }


        failure {

            echo "======================================"
            echo "PIPELINE STATUS: FAILURE"
            echo "Deployment failed or rollback was required."
            echo "Check console output for old/new/final state."
            echo "======================================"
        }


        always {

            echo "======================================"
            echo "PIPELINE COMPLETED"
            echo "======================================"
        }
    }
}