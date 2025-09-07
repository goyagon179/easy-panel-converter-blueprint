# Blueprint Framework - EasyPanel Quick Setup Guide

This guide will help you deploy the Blueprint Framework (Pterodactyl Panel with extensions) using EasyPanel.

## What is Blueprint Framework?

[Blueprint Framework](https://github.com/BlueprintFramework/docker) is an extension ecosystem for Pterodactyl Panel that provides a Docker-based deployment solution. It allows you to install, manage, and develop Pterodactyl modifications easily.

## Prerequisites

- EasyPanel account and access
- Domain name (optional, can use IP address)
- Basic understanding of Docker and Pterodactyl

## Quick Setup Steps

### 1. Import the Schema

1. **Download the schema file**: `blueprint-easypanel-schema-simple.json`
2. **Access EasyPanel**: Go to your EasyPanel dashboard
3. **Create new project**: Click "New Project"
4. **Import schema**: 
   - Go to Templates → Developer
   - Click "Create from Schema"
   - Paste the contents of `blueprint-easypanel-schema-simple.json`
   - Click "Create"

### 2. Configure Environment Variables

Before starting the services, you need to set these environment variables:

#### Required Variables:
```bash
# Database passwords (change these!)
DB_PASSWORD=your_secure_database_password
MYSQL_ROOT_PASSWORD=your_secure_root_password
REDIS_PASSWORD=your_secure_redis_password

# Wings configuration (get these from Pterodactyl Panel)
WINGS_UUID=your_wings_uuid_here
WINGS_TOKEN=your_wings_token_here
WINGS_NODE_ID=1
```

#### Optional Variables:
```bash
# Email configuration (for notifications)
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME=Pterodactyl Panel

# Application URL
APP_URL=https://yourdomain.com
```

### 3. Start the Services

1. **Start MySQL first**: Wait for it to be fully running
2. **Start Redis**: Wait for it to be fully running  
3. **Start Panel**: This will initialize the database
4. **Start Wings**: This connects to the panel

### 4. Initial Panel Setup

1. **Access the panel**: Go to `http://your-domain` or `http://your-ip`
2. **Complete setup wizard**: Follow the on-screen instructions
3. **Create admin user**: Set up your first administrator account
4. **Configure Wings**: Add the Wings daemon to your panel

### 5. Install Blueprint Extensions

1. **Upload extensions**: Place `.blueprint` files in the extensions volume
2. **Access panel container**: Use EasyPanel's terminal feature
3. **Install extensions**: Run `blueprint -i extension_name`

## Service Overview

| Service | Purpose | Ports | Dependencies |
|---------|---------|-------|--------------|
| **Panel** | Web interface | 80, 443 | MySQL, Redis |
| **MySQL** | Database | 3306 | None |
| **Redis** | Cache | 6379 | None |
| **Wings** | Game server daemon | 8080 | Panel |

## Important Notes

### Security
- **Change all default passwords** before going live
- **Use strong, unique passwords** for all services
- **Enable HTTPS** for production use
- **Restrict Wings port** (8080) if not needed externally

### Data Persistence
- All data is stored in Docker volumes
- **Backup regularly**: Especially `mysql_data` and `pterodactyl_app` volumes
- **Extensions**: Stored in the `extensions` volume

### Wings Configuration
- Wings requires access to the Docker socket (`/var/run/docker.sock`)
- This allows Wings to manage game server containers
- **Security consideration**: This gives Wings full Docker access

## Troubleshooting

### Common Issues

1. **Panel won't start**:
   - Check MySQL is running
   - Verify database credentials
   - Check logs for specific errors

2. **Wings can't connect**:
   - Verify `WINGS_TOKEN` and `WINGS_UUID`
   - Check `WINGS_REMOTE` URL
   - Ensure panel is accessible from Wings

3. **Database connection errors**:
   - Wait for MySQL to fully initialize
   - Check password configuration
   - Verify network connectivity

### Getting Help

- **Blueprint Framework**: [GitHub Issues](https://github.com/BlueprintFramework/docker/issues)
- **Pterodactyl Panel**: [Documentation](https://pterodactyl.io/)
- **EasyPanel**: [Documentation](https://easypanel.io/)

## Next Steps

1. **Configure your domain**: Set up proper DNS and SSL
2. **Install game servers**: Use the panel to create game server instances
3. **Install extensions**: Add Blueprint extensions for enhanced functionality
4. **Set up backups**: Implement regular backup strategy
5. **Monitor performance**: Use EasyPanel's monitoring features

## Files Included

- `blueprint-easypanel-schema-simple.json` - Main schema file
- `blueprint-easypanel-schema.json` - Advanced schema with networks
- `blueprint-docker-compose.yml` - Original Docker Compose file
- `BLUEPRINT_EASYPANEL_CONVERSION.md` - Detailed conversion documentation

---

**Ready to deploy?** Import the schema and follow the setup steps above!
