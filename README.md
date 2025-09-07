# Docker Compose to EasyPanel Schema Converter

A comprehensive Python tool that converts Docker Compose files to EasyPanel's `schema.json` format. This converter supports various service types, port mappings, environment variables, volumes, networks, and more.

## Features

- **Multi-Service Support**: Converts web applications, databases, and other services
- **Database Detection**: Automatically detects and converts popular databases (MySQL, PostgreSQL, MongoDB, Redis)
- **Port Mapping**: Handles both string and object port configurations
- **Environment Variables**: Converts environment variables in various formats
- **Volume Support**: Handles bind mounts and named volumes
- **Network Support**: Converts Docker networks
- **Dependency Management**: Preserves service dependencies
- **Comprehensive Error Handling**: Validates input and provides detailed error messages
- **CLI Interface**: Easy-to-use command-line interface

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python docker-compose-to-easypanel-converter.py -i docker-compose.yml -o schema.json
```

### Advanced Usage

```bash
# Specify project name
python docker-compose-to-easypanel-converter.py -i docker-compose.yml -p my-awesome-project

# Pretty print output
python docker-compose-to-easypanel-converter.py -i docker-compose.yml --pretty

# Validate input file
python docker-compose-to-easypanel-converter.py -i docker-compose.yml --validate
```

### Command Line Options

- `-i, --input`: Input Docker Compose file path (required)
- `-o, --output`: Output schema.json file path (default: schema.json)
- `-p, --project-name`: Project name for EasyPanel (default: my-project)
- `--pretty`: Pretty print the output JSON
- `--validate`: Validate the input Docker Compose file before conversion

## Supported Service Types

### Application Services
- **Type**: `app`
- **Features**: Image builds, port mappings, environment variables, volumes, commands
- **Examples**: Web applications, APIs, microservices

### Database Services
- **Supported Types**: `mysql`, `postgresql`, `mongodb`, `redis`
- **Auto-Detection**: Based on Docker image names
- **Environment Variables**: Automatically mapped to database-specific fields

## Example Conversions

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

## Supported Docker Compose Features

### Services
- ✅ Image-based services
- ✅ Build-based services (Dockerfile)
- ✅ Container names
- ✅ Port mappings (string and object format)
- ✅ Environment variables
- ✅ Volume mounts (bind and named volumes)
- ✅ Commands and entrypoints
- ✅ Restart policies
- ✅ Service dependencies
- ✅ Networks

### Databases
- ✅ MySQL/MariaDB
- ✅ PostgreSQL
- ✅ MongoDB
- ✅ Redis
- ✅ Custom database types via `EASYPANEL_DATABASE` environment variable

### Networks
- ✅ Bridge networks
- ✅ External networks
- ✅ Custom drivers
- ✅ Driver options

### Volumes
- ✅ Named volumes
- ✅ External volumes
- ✅ Driver options

## Database Environment Variable Mapping

### MySQL/MariaDB
- `MYSQL_ROOT_PASSWORD` → `rootPassword`
- `MYSQL_PASSWORD` → `password`
- `MYSQL_DATABASE` → `database`
- `MYSQL_USER` → `user`

### PostgreSQL
- `POSTGRES_PASSWORD` → `password`
- `POSTGRES_DB` → `database`
- `POSTGRES_USER` → `user`

### MongoDB
- `MONGO_INITDB_ROOT_PASSWORD` → `rootPassword`
- `MONGO_PASSWORD` → `password`
- `MONGO_INITDB_DATABASE` → `database`
- `MONGO_INITDB_ROOT_USERNAME` → `user`

### Redis
- `REDIS_PASSWORD` → `password`

## Error Handling

The converter includes comprehensive error handling for:

- Missing input files
- Invalid YAML syntax
- Unsupported Docker Compose features
- Missing required fields
- Invalid port configurations
- Volume mount errors

## Limitations

- Domains and proxies are not supported (configure manually in EasyPanel)
- Some advanced Docker Compose features may not be fully supported
- Custom network drivers may require manual configuration

## Examples

Check the `examples/` directory for sample Docker Compose files:

- `simple-app.yml`: Basic web application with database
- `complex-stack.yml`: Multi-service application with monitoring

## EasyPanel Integration

✅ **Working EasyPanel Schema**: `blueprint-easypanel-final.json`

This project includes a **tested and working** EasyPanel schema for the Blueprint Framework (Pterodactyl Panel with extensions). The schema has been validated and successfully imports into EasyPanel.

**Quick Start**:
1. Use `blueprint-easypanel-final.json` in EasyPanel's "Create from Schema" feature
2. Update the placeholder values after import
3. Deploy in order: MySQL → Redis → Panel → Wings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:

1. Check the examples in the `examples/` directory
2. Review the error messages for guidance
3. Open an issue on the project repository

## Changelog

### Version 1.0.0
- Initial release
- Support for basic Docker Compose features
- Database service detection and conversion
- CLI interface
- Comprehensive error handling
