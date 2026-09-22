# Retail Platform - DevOps Assessment

## Overview

Retail Platform is a Flask-based application containerized with Docker and deployed through Jenkins.

The project demonstrates:

- Git branching and release management
- Hotfix and merge workflows
- Intentional merge conflict resolution
- Jenkins parameterized deployment
- Docker image versioning
- Container health checks
- Deployment validation
- Automatic rollback after health-check failure
- Git commit and application-version traceability

## Project Structure

```text
retail-platform/
├── app/
│   ├── app.py
│   └── requirements.txt
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── README.md
└── .gitignore