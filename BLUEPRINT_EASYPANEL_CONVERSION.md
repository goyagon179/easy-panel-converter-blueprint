# Blueprint Framework Docker to EasyPanel Conversion

This document explains the conversion of the [BlueprintFramework/docker](https://github.com/BlueprintFramework/docker) project into an EasyPanel schema.json format.

## Overview

The Blueprint Framework is an extension ecosystem for Pterodactyl Panel that provides a Docker-based deployment solution. This conversion creates an EasyPanel-compatible schema that can be deployed directly in EasyPanel.

## Project Structure

The converted schema includes the following services:

### 1. **Pterodactyl Panel with Blueprint Framework** (`panel`)
- **Image**: `ghcr.io/blueprintframework/blueprint:latest`
- **Type**: Application service
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Purpose**: Main web interface for Pterodactyl Panel with Blueprint extensions
- **Dependencies**: MySQL, Redis

### 2. **MySQL Database** (`mysql`)
- **Image**: `mariadb:10.11`
- **Type**: MySQL database service
- **Purpose**: Stores panel data, user accounts, server configurations
- **Environment Variables**:
  - `MYSQL_ROOT_PASSWORD`: Root database password
  - `DB_PASSWORD`: Application database password
  - `DB_DATABASE`: Database name (pterodactyl)
  - `DB_USERNAME`: Database user (pterodactyl)

### 3. **Redis Cache** (`redis`)
- **Image**: `redis:7-alpine`
- **Type**: Redis service
- **Purpose**: Caching, session storage, queue management
- **Environment Variables**:
  - `REDIS_PASSWORD`: Redis authentication password

### 4. **Pterodactyl Wings** (`wings`)
- **Image**: `ghcr.io/pterodactyl/wings:latest`
- **Type**: Application service
- **Ports**: 8080 (API)
- **Purpose**: Game server daemon that manages individual game servers
- **Dependencies**: Panel
- **Special Volumes**: Docker socket for container management

### 5. **Nginx Reverse Proxy** (`nginx`)
- **Image**: `nginx:alpine`
- **Type**: Nginx service
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Purpose**: Reverse proxy, SSL termination, static file serving
- **Dependencies**: Panel

## Environment Variables

The following environment variables need to be configured in EasyPanel:

### Database Configuration
- `MYSQL_ROOT_PASSWORD`: MySQL root password
- `DB_PASSWORD`: Application database password
- `DB_DATABASE`: Database name (default: pterodactyl)
- `DB_USERNAME`: Database username (default: pterodactyl)

### Redis Configuration
- `REDIS_PASSWORD`: Redis authentication password

### Wings Configuration
- `WINGS_UUID`: Unique identifier for Wings daemon
- `WINGS_TOKEN`: Authentication token for Wings
- `WINGS_NODE_ID`: Node ID in Pterodactyl Panel
- `WINGS_REMOTE`: Panel URL (default: http://panel:80)

### Email Configuration
- `MAIL_HOST`: SMTP server hostname
- `MAIL_PORT`: SMTP server port (default: 587)
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password
- `MAIL_FROM_ADDRESS`: From email address
- `MAIL_FROM_NAME`: From name

### Application Configuration
- `APP_URL`: Public URL of the panel
- `APP_ENV`: Environment (production)
- `APP_DEBUG`: Debug mode (false)

## Volumes

The schema includes several persistent volumes:

1. **`pterodactyl_app`**: Panel application files and Blueprint extensions
2. **`mysql_data`**: MySQL database data
3. **`redis_data`**: Redis cache data
4. **`wings_data`**: Wings daemon data and server files
5. **`wings_logs`**: Wings daemon logs
6. **`extensions`**: Blueprint extension files

## Networks

- **`pterodactyl`**: Bridge network connecting all services

## Deployment Instructions

### 1. Import Schema into EasyPanel

1. Access your EasyPanel dashboard
2. Navigate to your project
3. Go to the **Templates** section
4. Scroll to the **Developer** section
5. Click **Create from Schema**
6. Paste the contents of `blueprint-easypanel-schema.json`
7. Click **Create**

### 2. Configure Environment Variables

Set the following environment variables in EasyPanel:

```bash
# Database
MYSQL_ROOT_PASSWORD=your_secure_root_password
DB_PASSWORD=your_secure_app_password
DB_DATABASE=pterodactyl
DB_USERNAME=pterodactyl

# Redis
REDIS_PASSWORD=your_secure_redis_password

# Wings
WINGS_UUID=your_wings_uuid
WINGS_TOKEN=your_wings_token
WINGS_NODE_ID=your_node_id
WINGS_REMOTE=http://panel:80

# Email (Optional)
MAIL_HOST=smtp.your-provider.com
MAIL_PORT=587
MAIL_USERNAME=your_email@domain.com
MAIL_PASSWORD=your_email_password
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME=Pterodactyl Panel

# Application
APP_URL=https://yourdomain.com
APP_ENV=production
APP_DEBUG=false
```

### 3. Configure Nginx (Optional)

If you're using the included Nginx service, you'll need to:

1. Create nginx configuration files
2. Mount them to the nginx service
3. Configure SSL certificates if using HTTPS

### 4. Initialize the Panel

After deployment, you'll need to:

1. Wait for all services to start
2. Access the panel through your domain
3. Complete the initial setup wizard
4. Create your first admin user

## Blueprint Extensions

To install Blueprint extensions:

1. Upload `.blueprint` files to the `extensions` volume
2. Access the panel container
3. Run: `blueprint -i extension_name`

## Backup Strategy

The following volumes should be backed up regularly:

- `pterodactyl_app`: Panel files and extensions
- `mysql_data`: Database data
- `wings_data`: Server files and configurations

## Security Considerations

1. **Change Default Passwords**: Ensure all default passwords are changed
2. **Use Strong Passwords**: Generate secure passwords for all services
3. **Enable HTTPS**: Configure SSL certificates for production use
4. **Firewall Rules**: Restrict access to Wings port (8080) if not needed externally
5. **Regular Updates**: Keep all images updated to latest versions

## Troubleshooting

### Common Issues

1. **Services Not Starting**: Check environment variables are set correctly
2. **Database Connection Errors**: Verify MySQL service is running and credentials are correct
3. **Wings Connection Issues**: Ensure WINGS_TOKEN and WINGS_UUID are valid
4. **Extension Installation**: Check file permissions on the extensions volume

### Logs

Access service logs through EasyPanel or by connecting to containers:

```bash
# Panel logs
docker logs pterodactyl-panel

# Wings logs
docker logs pterodactyl-wings

# MySQL logs
docker logs pterodactyl-mysql

# Redis logs
docker logs pterodactyl-redis
```

## Migration from Docker Compose

If migrating from the original Docker Compose setup:

1. Export your current data volumes
2. Import the EasyPanel schema
3. Restore your data to the new volumes
4. Update any external references to use the new service names

## Support

For issues related to:
- **Blueprint Framework**: [BlueprintFramework GitHub](https://github.com/BlueprintFramework)
- **Pterodactyl Panel**: [Pterodactyl Documentation](https://pterodactyl.io/)
- **EasyPanel**: [EasyPanel Documentation](https://easypanel.io/)

## License

This conversion maintains the same MIT license as the original BlueprintFramework project.
