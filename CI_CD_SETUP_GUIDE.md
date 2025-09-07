# EasyPanel CI/CD Setup Guide

This guide shows you the **easiest way** to set up Continuous Integration and Continuous Deployment (CI/CD) for automatically converting Docker Compose projects to EasyPanel.

## 🎯 **What This Achieves**

- **Automatic conversion** of Docker Compose to EasyPanel schema on every commit
- **Multi-environment deployments** (staging → production)
- **Schema validation** and health checks
- **Rollback capabilities** and error notifications
- **Zero-downtime deployments** with proper orchestration

## 🚀 **Quick Setup (5 Minutes)**

### 1. **Add GitHub Actions Workflow**

Copy the provided `.github/workflows/easypanel-deploy.yml` to your repository:

```bash
mkdir -p .github/workflows
cp easypanel-deploy.yml .github/workflows/
```

### 2. **Set GitHub Secrets**

In your GitHub repository settings → Secrets and variables → Actions, add:

```bash
# EasyPanel API Configuration
EASYPANEL_API_URL=https://your-easypanel-instance.com
EASYPANEL_API_TOKEN=your_api_token_here

# Project IDs
EASYPANEL_STAGING_PROJECT_ID=staging-project-id
EASYPANEL_PRODUCTION_PROJECT_ID=production-project-id

# Optional: Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
```

### 3. **Configure Your Project**

Copy and customize the configuration:

```bash
cp easypanel-config.example.yml easypanel-config.yml
# Edit easypanel-config.yml with your settings
```

### 4. **Test the Pipeline**

```bash
git add .
git commit -m "Add EasyPanel CI/CD pipeline"
git push origin main
```

**That's it!** 🎉 Your CI/CD pipeline is now active.

---

## 📋 **Detailed Setup Options**

### **Option 1: GitHub Actions (Recommended)**

**Pros:**
- ✅ Built into GitHub
- ✅ Free for public repos
- ✅ Great ecosystem
- ✅ Easy secret management

**Setup:**
1. Use the provided `easypanel-deploy.yml` workflow
2. Configure secrets in GitHub
3. Customize environment variables

### **Option 2: GitLab CI/CD**

Create `.gitlab-ci.yml`:

```yaml
stages:
  - convert
  - deploy-staging
  - deploy-production

variables:
  CONVERTER_IMAGE: python:3.11

convert-schema:
  stage: convert
  image: $CONVERTER_IMAGE
  script:
    - pip install PyYAML requests
    - python docker-compose-to-easypanel-converter-advanced.py -i docker-compose.yml -o schema.json -p "$CI_PROJECT_NAME"
  artifacts:
    paths:
      - schema.json
    expire_in: 1 hour

deploy-staging:
  stage: deploy-staging
  image: $CONVERTER_IMAGE
  script:
    - python scripts/deploy-to-easypanel.py --schema schema.json --environment staging --wait --health-check
  only:
    - main
  environment:
    name: staging
    url: https://staging.yourdomain.com

deploy-production:
  stage: deploy-production
  image: $CONVERTER_IMAGE
  script:
    - python scripts/deploy-to-easypanel.py --schema schema.json --environment production --wait --health-check
  only:
    - main
  when: manual
  environment:
    name: production
    url: https://yourdomain.com
```

### **Option 3: Jenkins Pipeline**

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    environment {
        EASYPANEL_API_URL = credentials('easypanel-api-url')
        EASYPANEL_API_TOKEN = credentials('easypanel-api-token')
    }
    
    stages {
        stage('Convert Schema') {
            steps {
                script {
                    sh '''
                        python3 docker-compose-to-easypanel-converter-advanced.py \
                            -i docker-compose.yml \
                            -o schema.json \
                            -p "${JOB_NAME}-${BRANCH_NAME}"
                    '''
                }
                archiveArtifacts artifacts: 'schema.json', fingerprint: true
            }
        }
        
        stage('Deploy to Staging') {
            when { branch 'main' }
            steps {
                script {
                    sh '''
                        python3 scripts/deploy-to-easypanel.py \
                            --schema schema.json \
                            --environment staging \
                            --wait --health-check
                    '''
                }
            }
        }
        
        stage('Deploy to Production') {
            when { 
                allOf {
                    branch 'main'
                    input message: 'Deploy to production?', ok: 'Deploy'
                }
            }
            steps {
                script {
                    sh '''
                        python3 scripts/deploy-to-easypanel.py \
                            --schema schema.json \
                            --environment production \
                            --wait --health-check
                    '''
                }
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'schema.json',
                reportName: 'EasyPanel Schema'
            ])
        }
    }
}
```

### **Option 4: Local Development Pipeline**

Create `deploy.sh` for local testing:

```bash
#!/bin/bash
set -e

# Configuration
ENVIRONMENT=${1:-staging}
COMPOSE_FILE=${2:-docker-compose.yml}
SCHEMA_FILE="schema-${ENVIRONMENT}.json"

echo "🚀 Deploying to ${ENVIRONMENT}..."

# Convert Docker Compose to EasyPanel schema
echo "📋 Converting Docker Compose to EasyPanel schema..."
python3 docker-compose-to-easypanel-converter-advanced.py \
    -i "$COMPOSE_FILE" \
    -o "$SCHEMA_FILE" \
    -p "local-$(basename $(pwd))" \
    --pretty

# Validate schema
echo "✅ Validating schema..."
python3 -c "import json; json.load(open('$SCHEMA_FILE'))"

# Deploy to EasyPanel
echo "🚀 Deploying to EasyPanel..."
python3 scripts/deploy-to-easypanel.py \
    --schema "$SCHEMA_FILE" \
    --environment "$ENVIRONMENT" \
    --wait \
    --health-check

echo "🎉 Deployment complete!"
```

Usage:
```bash
chmod +x deploy.sh
./deploy.sh staging          # Deploy to staging
./deploy.sh production       # Deploy to production
```

---

## 🔧 **Configuration Details**

### **Environment Variables**

| Variable | Description | Required |
|----------|-------------|----------|
| `EASYPANEL_API_URL` | Your EasyPanel instance URL | ✅ |
| `EASYPANEL_API_TOKEN` | API token for authentication | ✅ |
| `EASYPANEL_STAGING_PROJECT_ID` | Staging project ID | ✅ |
| `EASYPANEL_PRODUCTION_PROJECT_ID` | Production project ID | ✅ |
| `SLACK_WEBHOOK_URL` | Slack notifications | ❌ |
| `DISCORD_WEBHOOK_URL` | Discord notifications | ❌ |

### **Workflow Triggers**

The CI/CD pipeline triggers on:

1. **Push to main/master**: Deploys to staging automatically
2. **Manual workflow dispatch**: Choose environment manually
3. **Pull requests**: Validates schema only (no deployment)
4. **Production deployment**: Requires manual approval

### **Deployment Stages**

1. **Convert & Validate**: 
   - Converts Docker Compose to EasyPanel schema
   - Validates schema structure
   - Uploads artifacts

2. **Deploy to Staging**:
   - Deploys to staging environment
   - Runs health checks
   - Updates environment variables

3. **Deploy to Production**:
   - Requires manual approval
   - Deploys to production
   - Comprehensive health checks
   - Rollback on failure

---

## 🛡️ **Security Best Practices**

### **Secret Management**
```bash
# Store sensitive data as secrets, not in code
MYSQL_ROOT_PASSWORD="${{ secrets.MYSQL_ROOT_PASSWORD }}"
REDIS_PASSWORD="${{ secrets.REDIS_PASSWORD }}"
```

### **Environment Isolation**
```yaml
# Different databases for different environments
staging:
  DB_HOST: "staging-mysql"
production:
  DB_HOST: "production-mysql"
```

### **Access Control**
```yaml
# Require manual approval for production
deploy-production:
  environment: production
  when: manual
```

---

## 📊 **Monitoring & Notifications**

### **Slack Integration**
```yaml
- name: Notify Slack
  if: always()
  run: |
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"🚀 Deployment ${{ job.status }}: ${{ github.repository }}"}' \
      ${{ secrets.SLACK_WEBHOOK_URL }}
```

### **Health Checks**
```python
# Custom health check endpoints
health_endpoints = [
    "/health",
    "/api/health", 
    "/api/status"
]
```

### **Rollback Strategy**
```yaml
# Automatic rollback on failure
- name: Rollback on Failure
  if: failure()
  run: |
    python3 scripts/rollback.py --environment ${{ matrix.environment }}
```

---

## 🎯 **Advanced Features**

### **Multi-Environment Support**
- ✅ Staging, production, and custom environments
- ✅ Environment-specific configurations
- ✅ Automatic subdomain mapping

### **Schema Validation**
- ✅ JSON schema validation
- ✅ Service dependency checking
- ✅ Resource limit validation

### **Deployment Safety**
- ✅ Health checks before marking success
- ✅ Automatic rollback on failure
- ✅ Blue-green deployments

### **Integration Options**
- ✅ Works with any Git provider
- ✅ Supports multiple CI/CD platforms
- ✅ API-driven for custom integrations

---

## 🔧 **Troubleshooting**

### **Common Issues**

1. **API Authentication Failed**
   ```bash
   # Check your API token
   curl -H "Authorization: Bearer $EASYPANEL_API_TOKEN" \
        $EASYPANEL_API_URL/api/projects
   ```

2. **Schema Validation Failed**
   ```bash
   # Validate schema locally
   python3 -c "import json; print(json.load(open('schema.json'))['services'])"
   ```

3. **Deployment Timeout**
   ```bash
   # Increase timeout in workflow
   timeout: 600  # 10 minutes
   ```

### **Debug Mode**
```yaml
# Enable debug logging
- name: Debug Deployment
  env:
    DEBUG: true
  run: |
    python3 scripts/deploy-to-easypanel.py --schema schema.json --environment staging --debug
```

---

## 📚 **Next Steps**

1. **Set up monitoring**: Add Prometheus/Grafana for metrics
2. **Add testing**: Include integration tests in pipeline
3. **Implement GitOps**: Use ArgoCD or Flux for advanced deployments
4. **Add security scanning**: Include container security scans
5. **Performance optimization**: Add caching and parallel deployments

---

## 📞 **Support**

- **GitHub Issues**: [Your Repository Issues](https://github.com/yourusername/your-repo/issues)
- **Documentation**: Check the `docs/` folder
- **Community**: Join our Discord/Slack

**Ready to automate your deployments?** Follow the Quick Setup guide above! 🚀
