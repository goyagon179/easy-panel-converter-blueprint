# Docker Compose to EasyPanel Converter - Usage Guide

This comprehensive guide covers all aspects of using the Docker Compose to EasyPanel converter, from basic usage to advanced features.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Service Types](#service-types)
5. [Configuration Options](#configuration-options)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Quick Start

### Installation

1. **Clone or download the converter files**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Basic conversion:**
   ```bash
   python docker-compose-to-easypanel-converter.py -i docker-compose.yml -o schema.json
   ```

### Windows Users

Use the provided batch or PowerShell scripts:

```cmd
# Batch file
convert.bat docker-compose.yml schema.json my-project

# PowerShell
.\convert.ps1 -InputFile docker-compose.yml -OutputFile schema.json -ProjectName my-project
```

## Basic Usage

### Command Line Interface

```bash
python docker-compose-to-easypanel-converter.py [OPTIONS]
```

#### Required Arguments
- `-i, --input`: Path to Docker Compose file

#### Optional Arguments
- `-o, --output`: Output schema.json file path (default: schema.json)
- `-p, --project-name`: Project name for EasyPanel (default: my-project)
- `--pretty`: Pretty print the output JSON
- `--validate`: Validate input before conversion

### Examples

```bash
# Basic conversion
python docker-compose-to-easypanel-converter.py -i docker-compose.yml

# With custom project name
python docker-compose-to-easypanel-converter.py -i docker-compose.yml -p my-awesome-app

# Pretty print output
python docker-compose-to-easypanel-converter.py -i docker-compose.yml --pretty

# Validate input file
python docker-compose-to-easypanel-converter.py -i docker-compose.yml --validate
```

## Advanced Features

### Advanced Converter

For more features, use the advanced converter:

```bash
python docker-compose-to-easypanel-converter-advanced.py [OPTIONS]
```

#### Additional Options
- `--custom-types`: Custom service type mappings
- `--no-networks`: Skip network conversion
- `--no-volumes`: Skip volume conversion
- `--no-env-substitution`: Disable environment variable substitution

#### Examples

```bash
# Custom service type mapping
python docker-compose-to-easypanel-converter-advanced.py -i docker-compose.yml --custom-types "my-nginx:nginx,my-app:app"

# Skip networks and volumes
python docker-compose-to-easypanel-converter-advanced.py -i docker-compose.yml --no-networks --no-volumes

# Disable environment variable substitution
python docker-compose-to-easypanel-converter-advanced.py -i docker-compose.yml --no-env-substitution
```

## Service Types

### Supported Service Types

| Type | Description | Auto-Detection | Manual Override |
|------|-------------|----------------|-----------------|
| `app` | Generic application | Default | `EASYPANEL_SERVICE_TYPE=app` |
| `mysql` | MySQL database | `mysql`, `mariadb` | `EASYPANEL_SERVICE_TYPE=mysql` |
| `postgresql` | PostgreSQL database | `postgres`, `postgresql` | `EASYPANEL_SERVICE_TYPE=postgresql` |
| `mongodb` | MongoDB database | `mongo`, `mongodb` | `EASYPANEL_SERVICE_TYPE=mongodb` |
| `redis` | Redis cache | `redis` | `EASYPANEL_SERVICE_TYPE=redis` |
| `nginx` | Nginx web server | `nginx`, `caddy` | `EASYPANEL_SERVICE_TYPE=nginx` |
| `traefik` | Traefik proxy | `traefik` | `EASYPANEL_SERVICE_TYPE=traefik` |

### Database Service Configuration

#### MySQL/MariaDB
```yaml
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_PASSWORD: userpassword
      MYSQL_DATABASE: myapp
      MYSQL_USER: myuser
```

#### PostgreSQL
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: myapp
      POSTGRES_USER: user
```

#### MongoDB
```yaml
services:
  db:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_PASSWORD: rootpassword
      MONGO_PASSWORD: password
      MONGO_INITDB_DATABASE: myapp
      MONGO_INITDB_ROOT_USERNAME: admin
```

#### Redis
```yaml
services:
  cache:
    image: redis:7-alpine
    environment:
      REDIS_PASSWORD: password
```

## Configuration Options

### Environment Variable Substitution

The converter supports environment variable substitution:

```yaml
services:
  app:
    image: nginx:alpine
    environment:
      - API_URL=${API_URL:-http://localhost:8000}
      - DEBUG=${DEBUG:-false}
```

### Custom Service Types

Override service type detection:

```yaml
services:
  my-custom-service:
    image: custom-image:latest
    environment:
      EASYPANEL_SERVICE_TYPE: nginx
```

### Port Mappings

#### String Format
```yaml
ports:
  - "8080:80"
  - "3000:3000"
```

#### Object Format
```yaml
ports:
  - published: 8080
    target: 80
    protocol: tcp
  - published: 3000
    target: 3000
```

### Volume Mappings

#### Bind Mounts
```yaml
volumes:
  - ./html:/usr/share/nginx/html
  - /host/path:/container/path:ro
```

#### Named Volumes
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
  - redis_data:/data
```

#### Object Format
```yaml
volumes:
  - type: bind
    source: ./html
    target: /usr/share/nginx/html
    read_only: true
```

### Health Checks

```yaml
services:
  app:
    image: nginx:alpine
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Resource Limits

```yaml
services:
  app:
    image: nginx:alpine
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Logging Configuration

```yaml
services:
  app:
    image: nginx:alpine
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Examples

### Simple Web Application

**Input (docker-compose.yml):**
```yaml
version: "3.8"
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    environment:
      - NGINX_HOST=localhost
    volumes:
      - ./html:/usr/share/nginx/html

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
```

**Output (schema.json):**
```json
{
  "version": "1.0",
  "projectName": "my-project",
  "services": [
    {
      "type": "app",
      "data": {
        "projectName": "my-project",
        "serviceName": "web",
        "source": {
          "type": "image",
          "image": "nginx:alpine"
        },
        "ports": [
          {
            "published": 8080,
            "target": 80
          }
        ],
        "environment": {
          "NGINX_HOST": "localhost"
        },
        "volumes": [
          {
            "hostPath": "./html",
            "containerPath": "/usr/share/nginx/html"
          }
        ]
      }
    },
    {
      "type": "postgresql",
      "data": {
        "projectName": "my-project",
        "serviceName": "db",
        "database": "myapp",
        "user": "user",
        "password": "password"
      }
    }
  ]
}
```

### Complex Microservices Stack

See `examples/full-stack-example.yml` for a comprehensive example with:
- Frontend (React)
- Backend API (Django)
- Multiple databases (PostgreSQL, MongoDB, Redis)
- Message queue (RabbitMQ)
- Search engine (Elasticsearch)
- Monitoring (Prometheus, Grafana)
- Reverse proxy (Nginx, Traefik)
- File storage (MinIO)

## Troubleshooting

### Common Issues

#### 1. Python Not Found
**Error:** `Python was not found`

**Solution:**
- Install Python 3.7+ from [python.org](https://www.python.org/downloads/)
- Ensure Python is in your PATH
- Use `python3` instead of `python` if needed

#### 2. Missing Dependencies
**Error:** `ModuleNotFoundError: No module named 'yaml'`

**Solution:**
```bash
pip install -r requirements.txt
```

#### 3. Invalid YAML
**Error:** `Invalid YAML in Docker Compose file`

**Solution:**
- Validate your Docker Compose file syntax
- Use `--validate` flag to check before conversion
- Check for proper indentation and quotes

#### 4. Unsupported Features
**Error:** Some features not converted

**Solution:**
- Check the limitations section
- Use the advanced converter for more features
- Configure manually in EasyPanel dashboard

### Debug Mode

Enable verbose output for debugging:

```bash
python docker-compose-to-easypanel-converter.py -i docker-compose.yml --pretty
```

### Validation

Validate your Docker Compose file:

```bash
python docker-compose-to-easypanel-converter.py -i docker-compose.yml --validate
```

## Best Practices

### 1. Use Environment Variables
```yaml
services:
  app:
    image: nginx:alpine
    environment:
      - API_URL=${API_URL:-http://localhost:8000}
      - DEBUG=${DEBUG:-false}
```

### 2. Organize Services by Type
```yaml
services:
  # Web services
  frontend:
    # ...
  backend:
    # ...
  
  # Database services
  postgres:
    # ...
  redis:
    # ...
  
  # Monitoring services
  prometheus:
    # ...
  grafana:
    # ...
```

### 3. Use Named Volumes for Data
```yaml
volumes:
  postgres_data:
  redis_data:
  app_media:

services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 4. Configure Health Checks
```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 5. Set Resource Limits
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

### 6. Use Networks for Service Isolation
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
  monitoring:
    driver: bridge
```

## Testing

Run the test suite to verify functionality:

```bash
python test_suite.py
```

Run individual tests:

```bash
python test_converter.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

For issues and questions:
1. Check this documentation
2. Review the examples
3. Run the test suite
4. Open an issue with detailed information
