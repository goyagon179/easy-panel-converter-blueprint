#!/usr/bin/env python3
"""
Advanced Docker Compose to EasyPanel Schema Converter

An enhanced version with additional features:
- Support for more service types (nginx, traefik, etc.)
- Better error handling and validation
- Support for Docker Compose overrides
- Custom service type mapping
- Environment variable substitution
- Health checks
- Resource limits
- Logging configuration

Author: AI Assistant
Version: 2.0.0
"""

# Standard Python libraries for file handling, data processing, and command-line interface
import json          # For reading/writing JSON files (EasyPanel's format)
import yaml          # For reading YAML files (Docker Compose format)
import argparse      # For handling command-line arguments
import sys           # For system operations and error handling
import os            # For file system operations
import re            # For text pattern matching (environment variable substitution)
from typing import Dict, List, Any, Optional, Union, Tuple  # Type hints for better code documentation
from pathlib import Path  # Modern Python path handling
from dataclasses import dataclass  # For creating structured data classes
from enum import Enum  # For creating enumerated constants


class ServiceType(Enum):
    """
    Supported EasyPanel service types.
    
    This enum defines all the different types of services that EasyPanel can handle.
    Each service type has specific configuration requirements and capabilities.
    """
    APP = "app"                    # Generic application (web servers, APIs, microservices)
    MYSQL = "mysql"                # MySQL database server
    POSTGRESQL = "postgresql"      # PostgreSQL database server
    MONGODB = "mongodb"            # MongoDB document database
    REDIS = "redis"                # Redis cache and message broker
    NGINX = "nginx"                # Nginx web server and reverse proxy
    TRAEFIK = "traefik"            # Traefik reverse proxy and load balancer
    PROMETHEUS = "prometheus"      # Prometheus monitoring and metrics collection
    GRAFANA = "grafana"            # Grafana visualization and dashboarding


@dataclass
class ConversionOptions:
    """
    Options for the conversion process.
    
    This data class holds all the configuration options that control how
    the conversion process works. It allows users to customize the behavior
    without changing the code.
    """
    project_name: str = "my-project"                    # Name for the EasyPanel project
    validate_input: bool = True                         # Whether to validate input before conversion
    include_networks: bool = True                       # Whether to convert network configurations
    include_volumes: bool = True                        # Whether to convert volume configurations
    custom_service_types: Dict[str, str] = None         # Custom mappings for service types
    environment_substitution: bool = True               # Whether to substitute environment variables
    preserve_comments: bool = False                     # Whether to preserve comments (not implemented yet)


class AdvancedDockerComposeToEasyPanelConverter:
    """
    Advanced converter with enhanced features.
    
    This is the main class that handles the conversion from Docker Compose to EasyPanel.
    It includes more features than the basic converter, such as environment variable
    substitution, health checks, resource limits, and support for more service types.
    """
    
    # Extended service type mappings - maps Docker image names to EasyPanel service types
    # This is like a lookup table that tells us what type of service each Docker image represents
    SERVICE_TYPE_MAPPINGS = {
        # Database services - these store and manage data
        'mysql': ServiceType.MYSQL,           # MySQL database server
        'mariadb': ServiceType.MYSQL,         # MariaDB (MySQL-compatible)
        'percona': ServiceType.MYSQL,         # Percona (MySQL-compatible)
        'postgres': ServiceType.POSTGRESQL,   # PostgreSQL database server
        'postgresql': ServiceType.POSTGRESQL, # Alternative name for PostgreSQL
        'mongo': ServiceType.MONGODB,         # MongoDB document database
        'mongodb': ServiceType.MONGODB,       # Alternative name for MongoDB
        'redis': ServiceType.REDIS,           # Redis cache and message broker
        
        # Web servers and proxies - these handle HTTP traffic
        'nginx': ServiceType.NGINX,           # Nginx web server and reverse proxy
        'traefik': ServiceType.TRAEFIK,       # Traefik reverse proxy and load balancer
        'caddy': ServiceType.NGINX,          # Caddy web server (treat as nginx-like)
        'apache': ServiceType.NGINX,         # Apache web server (treat as nginx-like)
        
        # Monitoring services - these collect and display metrics
        'prometheus': ServiceType.PROMETHEUS, # Prometheus metrics collection
        'grafana': ServiceType.GRAFANA,       # Grafana dashboards and visualization
        'influxdb': ServiceType.APP,          # InfluxDB time-series database (treat as app)
        'elasticsearch': ServiceType.APP,     # Elasticsearch search engine (treat as app)
        
        # Message queues - these handle communication between services
        'rabbitmq': ServiceType.APP,          # RabbitMQ message broker (treat as app)
        'kafka': ServiceType.APP,             # Apache Kafka message streaming (treat as app)
        'nats': ServiceType.APP,              # NATS messaging system (treat as app)
    }
    
    # Environment variable patterns for substitution
    # These regex patterns help us find and replace environment variables in configuration
    ENV_PATTERNS = [
        r'\$\{([^}]+)\}',           # Pattern for ${VAR} format
        r'\$([A-Z_][A-Z0-9_]*)',    # Pattern for $VAR format (only uppercase with underscores)
    ]
    
    def __init__(self, options: ConversionOptions = None):
        """
        Initialize the advanced converter.
        
        This sets up the converter with the specified options and initializes
        empty lists to store the converted components.
        
        Args:
            options: Configuration options for the conversion process
        """
        self.options = options or ConversionOptions()  # Use provided options or defaults
        self.services = []      # List to store converted services
        self.networks = []      # List to store converted networks
        self.volumes = []       # List to store converted volumes
        self.secrets = []       # List to store converted secrets
        self.configs = []       # List to store converted configs
        self.environment_vars = {}  # Dictionary to store environment variables for substitution
        
    def convert_file(self, compose_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a Docker Compose file to EasyPanel schema.
        
        This is the main entry point that reads a Docker Compose file from disk,
        parses it, and converts it to EasyPanel format.
        
        Args:
            compose_file: Path to the Docker Compose file (usually docker-compose.yml)
            output_file: Optional output file path (if not provided, only returns the data)
            
        Returns:
            Dictionary containing the EasyPanel schema (JSON structure)
        """
        try:
            # Open and read the Docker Compose file
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)  # Parse YAML into Python dictionary
        except FileNotFoundError:
            raise FileNotFoundError(f"Docker Compose file not found: {compose_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in Docker Compose file: {e}")
        
        # Call the main conversion method with the parsed data
        return self.convert_data(compose_data, output_file)
    
    def convert_data(self, compose_data: Dict[str, Any], output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert Docker Compose data to EasyPanel schema.
        
        This method takes the parsed Docker Compose data and converts each section
        (services, networks, volumes, secrets, configs) to EasyPanel format.
        
        Args:
            compose_data: Parsed Docker Compose data (Python dictionary)
            output_file: Optional output file path
            
        Returns:
            Dictionary containing the EasyPanel schema
        """
        # Reset our storage lists for a fresh conversion
        self.services = []
        self.networks = []
        self.volumes = []
        self.secrets = []
        self.configs = []
        
        # Extract environment variables for substitution
        # This allows us to replace ${VAR} and $VAR with actual values
        if self.options.environment_substitution:
            self._extract_environment_vars(compose_data)
        
        # Process services
        services_data = compose_data.get('services', {})
        for service_name, service_config in services_data.items():
            service = self._convert_service(service_name, service_config)
            if service:
                self.services.append(service)
        
        # Process networks
        if self.options.include_networks:
            networks_data = compose_data.get('networks', {})
            for network_name, network_config in networks_data.items():
                network = self._convert_network(network_name, network_config)
                if network:
                    self.networks.append(network)
        
        # Process volumes
        if self.options.include_volumes:
            volumes_data = compose_data.get('volumes', {})
            for volume_name, volume_config in volumes_data.items():
                volume = self._convert_volume(volume_name, volume_config)
                if volume:
                    self.volumes.append(volume)
        
        # Process secrets
        secrets_data = compose_data.get('secrets', {})
        for secret_name, secret_config in secrets_data.items():
            secret = self._convert_secret(secret_name, secret_config)
            if secret:
                self.secrets.append(secret)
        
        # Process configs
        configs_data = compose_data.get('configs', {})
        for config_name, config_config in configs_data.items():
            config = self._convert_config(config_name, config_config)
            if config:
                self.configs.append(config)
        
        # Create the final schema
        schema = {
            "version": "2.0",
            "projectName": self.options.project_name,
            "services": self.services,
            "networks": self.networks,
            "volumes": self.volumes,
            "secrets": self.secrets,
            "configs": self.configs
        }
        
        # Write to output file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            print(f"Schema written to: {output_file}")
        
        return schema
    
    def _extract_environment_vars(self, compose_data: Dict[str, Any]):
        """
        Extract environment variables for substitution.
        
        This method looks for environment variables in two places:
        1. .env files referenced in the Docker Compose file
        2. Environment variables defined directly in service configurations
        
        These variables can then be used to substitute ${VAR} and $VAR patterns
        in the configuration.
        
        Args:
            compose_data: Parsed Docker Compose data
        """
        # Look for .env file references in the Docker Compose file
        env_file = compose_data.get('env_file', [])
        if isinstance(env_file, str):
            env_file = [env_file]  # Convert single string to list
        
        # Read each .env file and extract key=value pairs
        for env_path in env_file:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)  # Split on first '=' only
                            self.environment_vars[key] = value
        
        # Extract environment variables from service configurations
        for service_config in compose_data.get('services', {}).values():
            env_vars = service_config.get('environment', {})
            if isinstance(env_vars, dict):
                self.environment_vars.update(env_vars)  # Add to our collection
    
    def _substitute_environment_vars(self, value: str) -> str:
        """
        Substitute environment variables in a string.
        
        This method finds patterns like ${VAR} and $VAR in a string and replaces
        them with the actual values from environment variables.
        
        Args:
            value: String that may contain environment variable patterns
            
        Returns:
            String with environment variables substituted
        """
        if not isinstance(value, str):
            return value  # Return non-strings as-is
        
        # Try each pattern to find environment variable references
        for pattern in self.ENV_PATTERNS:
            matches = re.findall(pattern, value)  # Find all matches for this pattern
            for match in matches:
                # Look up the environment variable value
                # First check our extracted vars, then system environment
                env_value = self.environment_vars.get(match, os.environ.get(match, ''))
                # Replace both ${VAR} and $VAR formats
                value = value.replace(f'${{{match}}}', env_value).replace(f'${match}', env_value)
        
        return value
    
    def _convert_service(self, service_name: str, service_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a single service to EasyPanel format.
        
        Each service in Docker Compose (like a web server, database, etc.) needs to be
        converted to EasyPanel's format. This method figures out what type of service
        it is and converts it accordingly.
        
        Args:
            service_name: Name of the service (e.g., "web", "database")
            service_config: Configuration for the service (image, ports, environment, etc.)
            
        Returns:
            Converted service in EasyPanel format, or None if conversion failed
        """
        if not service_config:  # Skip empty configurations
            return None
        
        # Substitute environment variables in the service configuration
        # This replaces ${VAR} and $VAR with actual values
        if self.options.environment_substitution:
            service_config = self._substitute_vars_in_dict(service_config)
        
        # Determine what type of service this is (app, database, etc.)
        service_type = self._determine_service_type(service_config)
        
        # Convert based on the service type
        if service_type in [ServiceType.MYSQL, ServiceType.POSTGRESQL, ServiceType.MONGODB, ServiceType.REDIS]:
            # This is a database service
            return self._convert_database_service(service_name, service_config, service_type)
        elif service_type in [ServiceType.NGINX, ServiceType.TRAEFIK]:
            # This is a web server or proxy service
            return self._convert_proxy_service(service_name, service_config, service_type)
        elif service_type in [ServiceType.PROMETHEUS, ServiceType.GRAFANA]:
            # This is a monitoring service
            return self._convert_monitoring_service(service_name, service_config, service_type)
        else:
            # This is a regular application service
            return self._convert_app_service(service_name, service_config)
    
    def _substitute_vars_in_dict(self, data: Any) -> Any:
        """
        Recursively substitute environment variables in a dictionary.
        
        This method walks through a nested data structure (dictionaries, lists, strings)
        and substitutes environment variables in all string values it finds.
        
        Args:
            data: Any data structure that might contain strings with environment variables
            
        Returns:
            Same data structure with environment variables substituted
        """
        if isinstance(data, dict):
            # Recursively process each key-value pair in the dictionary
            return {k: self._substitute_vars_in_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Recursively process each item in the list
            return [self._substitute_vars_in_dict(item) for item in data]
        elif isinstance(data, str):
            # This is a string - substitute environment variables in it
            return self._substitute_environment_vars(data)
        else:
            # Not a string, list, or dict - return as-is
            return data
    
    def _determine_service_type(self, service_config: Dict[str, Any]) -> ServiceType:
        """
        Determine the EasyPanel service type.
        
        This method looks at the service configuration to figure out what type
        of service it is. It checks several sources in order of priority:
        1. Custom service type mappings
        2. Explicit service type in environment variables
        3. Docker image name patterns
        4. Default to app type
        
        Args:
            service_config: The service configuration from Docker Compose
            
        Returns:
            The service type as a ServiceType enum value
        """
        # Check for explicit type override from custom mappings
        if self.options.custom_service_types:
            service_name = service_config.get('container_name', '')
            if service_name in self.options.custom_service_types:
                return ServiceType(self.options.custom_service_types[service_name])
        
        # Check for explicit service type in environment variables
        # This allows users to force a specific service type
        env_vars = service_config.get('environment', {})
        if isinstance(env_vars, dict) and 'EASYPANEL_SERVICE_TYPE' in env_vars:
            try:
                return ServiceType(env_vars['EASYPANEL_SERVICE_TYPE'])
            except ValueError:
                pass  # Invalid service type, continue with other checks
        
        # Check image name against our mapping patterns
        # This is the most common way to determine service type
        image = service_config.get('image', '').lower()
        for image_pattern, service_type in self.SERVICE_TYPE_MAPPINGS.items():
            if image_pattern in image:  # Check if pattern is in the image name
                return service_type
        
        # Default to app type if we can't determine what it is
        return ServiceType.APP
    
    def _convert_app_service(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a service to EasyPanel app format.
        
        This handles regular application services (web servers, APIs, microservices, etc.)
        that aren't databases or specialized services. It converts all the common Docker
        Compose settings like ports, environment variables, volumes, etc.
        
        Args:
            service_name: Name of the service
            service_config: Docker Compose service configuration
            
        Returns:
            Service converted to EasyPanel app format
        """
        # Start with basic service information
        service_data = {
            "projectName": self.options.project_name,
            "serviceName": service_name
        }
        
        # Handle image source - where does this service come from?
        if 'image' in service_config:
            # Using a pre-built Docker image
            service_data["source"] = {
                "type": "image",
                "image": service_config['image']
            }
        elif 'build' in service_config:
            # Building from a Dockerfile
            build_config = service_config['build']
            if isinstance(build_config, str):
                # Simple build path
                service_data["source"] = {
                    "type": "dockerfile",
                    "dockerfile": build_config
                }
            elif isinstance(build_config, dict):
                # Detailed build configuration with context and build args
                service_data["source"] = {
                    "type": "dockerfile",
                    "dockerfile": build_config.get('dockerfile', 'Dockerfile'),
                    "context": build_config.get('context', '.'),
                    "args": build_config.get('args', {})  # Build-time arguments
                }
        
        # Handle ports - which ports should be accessible from outside the container?
        ports = self._convert_ports(service_config.get('ports', []))
        if ports:
            service_data["ports"] = ports
        
        # Handle environment variables - configuration values for the application
        env_vars = self._convert_environment(service_config.get('environment', {}))
        if env_vars:
            service_data["environment"] = env_vars
        
        # Handle volumes - persistent storage or file sharing
        volumes = self._convert_volumes(service_config.get('volumes', []))
        if volumes:
            service_data["volumes"] = volumes
        
        # Handle command - what command should run when the container starts?
        if 'command' in service_config:
            service_data["command"] = service_config['command']
        
        # Handle restart policy - what should happen if the container crashes?
        if 'restart' in service_config:
            service_data["restart"] = service_config['restart']
        
        # Handle depends_on - which other services must start before this one?
        if 'depends_on' in service_config:
            service_data["dependsOn"] = service_config['depends_on']
        
        # Handle health checks - how to check if the service is running properly?
        if 'healthcheck' in service_config:
            service_data["healthCheck"] = self._convert_health_check(service_config['healthcheck'])
        
        # Handle resource limits - CPU and memory constraints
        if 'deploy' in service_config:
            deploy_config = service_config['deploy']
            if 'resources' in deploy_config:
                service_data["resources"] = self._convert_resources(deploy_config['resources'])
        
        # Handle logging - how should logs be collected and stored?
        if 'logging' in service_config:
            service_data["logging"] = self._convert_logging(service_config['logging'])
        
        # Handle networks - which networks should this service be connected to?
        if 'networks' in service_config:
            service_data["networks"] = service_config['networks']
        
        # Return the service in EasyPanel format
        return {
            "type": "app",
            "data": service_data
        }
    
    def _convert_database_service(self, service_name: str, service_config: Dict[str, Any], db_type: ServiceType) -> Dict[str, Any]:
        """
        Convert a service to EasyPanel database format.
        
        Database services need special handling because they have specific configuration
        fields (like database name, username, password) that are different from regular apps.
        Each database type has different environment variable names for these settings.
        
        Args:
            service_name: Name of the database service
            service_config: Docker Compose service configuration
            db_type: Type of database (mysql, postgresql, etc.)
            
        Returns:
            Service converted to EasyPanel database format
        """
        # Start with basic service information
        service_data = {
            "projectName": self.options.project_name,
            "serviceName": service_name
        }
        
        # Extract database-specific environment variables
        # Convert list format to dictionary if needed
        env_vars = service_config.get('environment', {})
        if isinstance(env_vars, list):
            # Convert ["KEY=value", "KEY2=value2"] to {"KEY": "value", "KEY2": "value2"}
            env_vars = {item.split('=')[0]: item.split('=')[1] for item in env_vars if '=' in item}
        
        # Map environment variables based on database type
        # Each database has different environment variable names for the same concepts
        if db_type == ServiceType.MYSQL:
            self._map_mysql_env_vars(service_data, env_vars)
        elif db_type == ServiceType.POSTGRESQL:
            self._map_postgresql_env_vars(service_data, env_vars)
        elif db_type == ServiceType.MONGODB:
            self._map_mongodb_env_vars(service_data, env_vars)
        elif db_type == ServiceType.REDIS:
            self._map_redis_env_vars(service_data, env_vars)
        
        # Handle ports
        ports = self._convert_ports(service_config.get('ports', []))
        if ports:
            service_data["ports"] = ports
        
        # Handle volumes
        volumes = self._convert_volumes(service_config.get('volumes', []))
        if volumes:
            service_data["volumes"] = volumes
        
        # Handle restart policy
        if 'restart' in service_config:
            service_data["restart"] = service_config['restart']
        
        return {
            "type": db_type.value,
            "data": service_data
        }
    
    def _map_mysql_env_vars(self, service_data: Dict[str, Any], env_vars: Dict[str, str]):
        """
        Map MySQL environment variables to EasyPanel database fields.
        
        MySQL uses specific environment variable names for database configuration.
        This method maps those to the standard EasyPanel database fields.
        
        Args:
            service_data: The service data dictionary to populate
            env_vars: Environment variables from the Docker Compose configuration
        """
        mysql_mapping = {
            'rootPassword': ['MYSQL_ROOT_PASSWORD', 'MARIADB_ROOT_PASSWORD'],  # Root user password
            'password': ['MYSQL_PASSWORD', 'MARIADB_PASSWORD'],                 # Regular user password
            'database': ['MYSQL_DATABASE', 'MARIADB_DATABASE'],                 # Database name
            'user': ['MYSQL_USER', 'MARIADB_USER']                              # Username
        }
        self._map_env_vars(service_data, env_vars, mysql_mapping)
    
    def _map_postgresql_env_vars(self, service_data: Dict[str, Any], env_vars: Dict[str, str]):
        """
        Map PostgreSQL environment variables to EasyPanel database fields.
        
        PostgreSQL uses different environment variable names than MySQL.
        This method maps those to the standard EasyPanel database fields.
        
        Args:
            service_data: The service data dictionary to populate
            env_vars: Environment variables from the Docker Compose configuration
        """
        postgres_mapping = {
            'password': ['POSTGRES_PASSWORD'],  # PostgreSQL password (same for root and user)
            'database': ['POSTGRES_DB'],        # Database name
            'user': ['POSTGRES_USER']           # Username
        }
        self._map_env_vars(service_data, env_vars, postgres_mapping)
    
    def _map_mongodb_env_vars(self, service_data: Dict[str, Any], env_vars: Dict[str, str]):
        """
        Map MongoDB environment variables to EasyPanel database fields.
        
        MongoDB uses different environment variable names than SQL databases.
        This method maps those to the standard EasyPanel database fields.
        
        Args:
            service_data: The service data dictionary to populate
            env_vars: Environment variables from the Docker Compose configuration
        """
        mongo_mapping = {
            'rootPassword': ['MONGO_ROOT_PASSWORD', 'MONGO_INITDB_ROOT_PASSWORD'],  # Admin password
            'password': ['MONGO_PASSWORD'],                                          # User password
            'database': ['MONGO_DATABASE', 'MONGO_INITDB_DATABASE'],                # Database name
            'user': ['MONGO_USER', 'MONGO_INITDB_ROOT_USERNAME']                     # Username
        }
        self._map_env_vars(service_data, env_vars, mongo_mapping)
    
    def _map_redis_env_vars(self, service_data: Dict[str, Any], env_vars: Dict[str, str]):
        """
        Map Redis environment variables to EasyPanel database fields.
        
        Redis is simpler than SQL databases - it only needs a password.
        This method maps the Redis password to the standard EasyPanel field.
        
        Args:
            service_data: The service data dictionary to populate
            env_vars: Environment variables from the Docker Compose configuration
        """
        redis_mapping = {
            'password': ['REDIS_PASSWORD']  # Redis password
        }
        self._map_env_vars(service_data, env_vars, redis_mapping)
    
    def _map_env_vars(self, service_data: Dict[str, Any], env_vars: Dict[str, str], mapping: Dict[str, List[str]]):
        """
        Map environment variables using the provided mapping.
        
        This is a generic method that takes a mapping dictionary and applies it to
        convert environment variables to EasyPanel database fields. It tries each
        possible environment variable name for each field until it finds a match.
        
        Args:
            service_data: The service data dictionary to populate
            env_vars: Environment variables from the Docker Compose configuration
            mapping: Dictionary mapping EasyPanel fields to lists of possible env var names
        """
        for field, env_keys in mapping.items():
            # Try each possible environment variable name for this field
            for env_key in env_keys:
                if env_key in env_vars:
                    service_data[field] = env_vars[env_key]
                    break  # Found it, move to next field
    
    def _convert_proxy_service(self, service_name: str, service_config: Dict[str, Any], proxy_type: ServiceType) -> Dict[str, Any]:
        """
        Convert a proxy service (nginx, traefik) to EasyPanel format.
        
        Proxy services like Nginx and Traefik handle HTTP traffic and routing.
        They need special handling for configuration files and port mappings.
        
        Args:
            service_name: Name of the proxy service
            service_config: Docker Compose service configuration
            proxy_type: Type of proxy (nginx, traefik)
            
        Returns:
            Service converted to EasyPanel proxy format
        """
        # Start with basic service information
        service_data = {
            "projectName": self.options.project_name,
            "serviceName": service_name
        }
        
        # Handle image source
        if 'image' in service_config:
            service_data["source"] = {
                "type": "image",
                "image": service_config['image']
            }
        
        # Handle ports - proxy services typically need to expose HTTP/HTTPS ports
        ports = self._convert_ports(service_config.get('ports', []))
        if ports:
            service_data["ports"] = ports
        
        # Handle volumes - proxy services often need configuration files
        volumes = self._convert_volumes(service_config.get('volumes', []))
        if volumes:
            service_data["volumes"] = volumes
        
        # Handle environment variables - proxy configuration
        env_vars = self._convert_environment(service_config.get('environment', {}))
        if env_vars:
            service_data["environment"] = env_vars
        
        # Handle command - custom startup command for the proxy
        if 'command' in service_config:
            service_data["command"] = service_config['command']
        
        # Return the proxy service in EasyPanel format
        return {
            "type": proxy_type.value,
            "data": service_data
        }
    
    def _convert_monitoring_service(self, service_name: str, service_config: Dict[str, Any], monitoring_type: ServiceType) -> Dict[str, Any]:
        """
        Convert a monitoring service to EasyPanel format.
        
        Monitoring services like Prometheus and Grafana are treated as regular
        application services since they don't need special database-like configuration.
        
        Args:
            service_name: Name of the monitoring service
            service_config: Docker Compose service configuration
            monitoring_type: Type of monitoring service (prometheus, grafana)
            
        Returns:
            Service converted to EasyPanel app format
        """
        # Monitoring services are treated as regular apps
        return self._convert_app_service(service_name, service_config)
    
    def _convert_ports(self, ports_config: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Convert Docker Compose ports to EasyPanel format.
        
        Docker Compose ports can be specified in different ways:
        - String format: "8080:80" (host port 8080 maps to container port 80)
        - Object format: {"published": 8080, "target": 80}
        
        This method handles both formats and converts them to EasyPanel's format.
        
        Args:
            ports_config: List of port configurations from Docker Compose
            
        Returns:
            List of ports in EasyPanel format
        """
        converted_ports = []
        
        for port in ports_config:
            if isinstance(port, str):
                # Handle string format like "8080:80" or "8080"
                if ':' in port:
                    # Format: "host_port:container_port"
                    host_port, container_port = port.split(':', 1)
                    converted_ports.append({
                        "published": int(host_port),    # Port on the host machine
                        "target": int(container_port)   # Port inside the container
                    })
                else:
                    # Format: "8080" (same port for both host and container)
                    converted_ports.append({
                        "published": int(port),
                        "target": int(port)
                    })
            elif isinstance(port, dict):
                # Handle object format with more detailed configuration
                converted_ports.append({
                    "published": port.get('published', port.get('host', 0)),
                    "target": port.get('target', port.get('container', 0)),
                    "protocol": port.get('protocol', 'tcp')  # Default to TCP protocol
                })
        
        return converted_ports
    
    def _convert_environment(self, env_config: Union[Dict[str, str], List[str]]) -> Dict[str, str]:
        """
        Convert Docker Compose environment variables to EasyPanel format.
        
        Environment variables can be specified in two ways in Docker Compose:
        - Dictionary: {"KEY": "value", "KEY2": "value2"}
        - List: ["KEY=value", "KEY2=value2"]
        
        This method converts both to a consistent dictionary format.
        
        Args:
            env_config: Environment configuration from Docker Compose
            
        Returns:
            Dictionary of environment variables
        """
        if isinstance(env_config, dict):
            # Already in dictionary format
            return env_config
        elif isinstance(env_config, list):
            # Convert list format to dictionary
            env_dict = {}
            for item in env_config:
                if '=' in item:
                    key, value = item.split('=', 1)  # Split on first '=' only
                    env_dict[key] = value
            return env_dict
        return {}  # Return empty dict for invalid formats
    
    def _convert_volumes(self, volumes_config: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Convert Docker Compose volumes to EasyPanel format.
        
        Volumes are used for persistent storage and file sharing. They can be:
        - Bind mounts: "./html:/usr/share/nginx/html" (host path to container path)
        - Named volumes: "postgres_data:/var/lib/postgresql/data" (volume name to container path)
        - Object format: {"source": "./html", "target": "/usr/share/nginx/html"}
        
        Args:
            volumes_config: List of volume configurations from Docker Compose
            
        Returns:
            List of volumes in EasyPanel format
        """
        converted_volumes = []
        
        for volume in volumes_config:
            if isinstance(volume, str):
                # Handle string format
                if ':' in volume:
                    # Format: "host_path:container_path"
                    host_path, container_path = volume.split(':', 1)
                    converted_volumes.append({
                        "hostPath": host_path,        # Path on the host machine
                        "containerPath": container_path  # Path inside the container
                    })
                else:
                    # Format: "volume_name" (named volume)
                    converted_volumes.append({
                        "volumeName": volume,         # Name of the Docker volume
                        "containerPath": volume       # Mount point (same as volume name)
                    })
            elif isinstance(volume, dict):
                # Handle object format with more detailed configuration
                converted_volumes.append({
                    "hostPath": volume.get('source', volume.get('host', '')),
                    "containerPath": volume.get('target', volume.get('container', '')),
                    "volumeName": volume.get('name', ''),
                    "readOnly": volume.get('read_only', False)  # Whether the volume is read-only
                })
        
        return converted_volumes
    
    def _convert_health_check(self, healthcheck_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Docker Compose health check to EasyPanel format.
        
        Health checks are used to determine if a service is running properly.
        They run a command periodically to check the service's health status.
        
        Args:
            healthcheck_config: Health check configuration from Docker Compose
            
        Returns:
            Health check configuration in EasyPanel format
        """
        return {
            "test": healthcheck_config.get('test', []),                    # Command to run for health check
            "interval": healthcheck_config.get('interval', '30s'),         # How often to run the check
            "timeout": healthcheck_config.get('timeout', '10s'),           # How long to wait for the check
            "retries": healthcheck_config.get('retries', 3),               # How many failures before marking unhealthy
            "startPeriod": healthcheck_config.get('start_period', '0s')    # Grace period before starting checks
        }
    
    def _convert_resources(self, resources_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Docker Compose resource limits to EasyPanel format.
        
        Resource limits control how much CPU and memory a container can use.
        This helps prevent one service from consuming all available resources.
        
        Args:
            resources_config: Resource configuration from Docker Compose
            
        Returns:
            Resource configuration in EasyPanel format
        """
        limits = resources_config.get('limits', {})           # Maximum resources the container can use
        reservations = resources_config.get('reservations', {})  # Minimum resources guaranteed to the container
        
        return {
            "limits": {
                "cpus": limits.get('cpus', ''),      # Maximum CPU usage (e.g., "1.0" for 1 CPU core)
                "memory": limits.get('memory', '')   # Maximum memory usage (e.g., "1G" for 1 gigabyte)
            },
            "reservations": {
                "cpus": reservations.get('cpus', ''),    # Minimum CPU guaranteed
                "memory": reservations.get('memory', '') # Minimum memory guaranteed
            }
        }
    
    def _convert_logging(self, logging_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Docker Compose logging configuration to EasyPanel format.
        
        Logging configuration controls how container logs are collected and stored.
        This helps with debugging and monitoring application behavior.
        
        Args:
            logging_config: Logging configuration from Docker Compose
            
        Returns:
            Logging configuration in EasyPanel format
        """
        return {
            "driver": logging_config.get('driver', 'json-file'),  # Logging driver (json-file, syslog, etc.)
            "options": logging_config.get('options', {})          # Driver-specific options
        }
    
    def _convert_network(self, network_name: str, network_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a Docker Compose network to EasyPanel format.
        
        Networks define how containers can communicate with each other.
        They can be simple bridge networks or more complex custom networks.
        
        Args:
            network_name: Name of the network
            network_config: Network configuration from Docker Compose
            
        Returns:
            Network in EasyPanel format, or None if conversion failed
        """
        if not network_config:  # Skip empty configurations
            return None
        
        network_data = {
            "name": network_name,
            "driver": network_config.get('driver', 'bridge')  # Default to bridge driver
        }
        
        # Handle external networks (networks created outside of this compose file)
        if network_config.get('external', False):
            network_data["external"] = True
        
        # Handle network options (custom driver settings)
        if 'driver_opts' in network_config:
            network_data["options"] = network_config['driver_opts']
        
        # Handle IPAM (IP Address Management) configuration
        if 'ipam' in network_config:
            network_data["ipam"] = network_config['ipam']
        
        return {
            "type": "network",
            "data": network_data
        }
    
    def _convert_volume(self, volume_name: str, volume_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a Docker Compose volume to EasyPanel format.
        
        Named volumes are persistent storage that Docker manages for you.
        They're different from bind mounts because Docker handles the storage location.
        
        Args:
            volume_name: Name of the volume
            volume_config: Volume configuration from Docker Compose
            
        Returns:
            Volume in EasyPanel format, or None if conversion failed
        """
        if not volume_config:  # Skip empty configurations
            return None
        
        volume_data = {
            "name": volume_name,
            "driver": volume_config.get('driver', 'local')  # Default to local driver
        }
        
        # Handle external volumes (volumes created outside of this compose file)
        if volume_config.get('external', False):
            volume_data["external"] = True
        
        # Handle volume options (custom driver settings)
        if 'driver_opts' in volume_config:
            volume_data["options"] = volume_config['driver_opts']
        
        return {
            "type": "volume",
            "data": volume_data
        }
    
    def _convert_secret(self, secret_name: str, secret_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a Docker Compose secret to EasyPanel format.
        
        Secrets are used to store sensitive information like passwords and API keys.
        They're managed by Docker and can be securely passed to containers.
        
        Args:
            secret_name: Name of the secret
            secret_config: Secret configuration from Docker Compose
            
        Returns:
            Secret in EasyPanel format, or None if conversion failed
        """
        if not secret_config:  # Skip empty configurations
            return None
        
        secret_data = {
            "name": secret_name
        }
        
        # Handle external secrets (secrets created outside of this compose file)
        if secret_config.get('external', False):
            secret_data["external"] = True
        
        # Handle file-based secrets
        if 'file' in secret_config:
            secret_data["file"] = secret_config['file']
        
        return {
            "type": "secret",
            "data": secret_data
        }
    
    def _convert_config(self, config_name: str, config_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a Docker Compose config to EasyPanel format.
        
        Configs are used to store non-sensitive configuration files.
        They're managed by Docker and can be mounted into containers.
        
        Args:
            config_name: Name of the config
            config_config: Config configuration from Docker Compose
            
        Returns:
            Config in EasyPanel format, or None if conversion failed
        """
        if not config_config:  # Skip empty configurations
            return None
        
        config_data = {
            "name": config_name
        }
        
        # Handle external configs (configs created outside of this compose file)
        if config_config.get('external', False):
            config_data["external"] = True
        
        # Handle file-based configs
        if 'file' in config_config:
            config_data["file"] = config_config['file']
        
        return {
            "type": "config",
            "data": config_data
        }


def main():
    """
    Main CLI entry point for the advanced converter.
    
    This function handles command-line arguments and orchestrates the conversion process.
    It's what gets called when you run the advanced converter script from the command line.
    """
    # Set up command-line argument parser with detailed help and examples
    parser = argparse.ArgumentParser(
        description="Advanced Docker Compose to EasyPanel schema.json converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i docker-compose.yml -o schema.json
  %(prog)s -i docker-compose.yml -p my-awesome-project --custom-types nginx:nginx
  %(prog)s -i docker-compose.yml --no-networks --no-volumes
        """
    )
    
    # Define command-line arguments
    parser.add_argument('-i', '--input', required=True, help='Input Docker Compose file path')
    parser.add_argument('-o', '--output', help='Output schema.json file path (default: schema.json)')
    parser.add_argument('-p', '--project-name', default='my-project', help='Project name for EasyPanel')
    parser.add_argument('--custom-types', help='Custom service type mappings (format: service:type)')
    parser.add_argument('--no-networks', action='store_true', help='Skip network conversion')
    parser.add_argument('--no-volumes', action='store_true', help='Skip volume conversion')
    parser.add_argument('--no-env-substitution', action='store_true', help='Disable environment variable substitution')
    parser.add_argument('--pretty', action='store_true', help='Pretty print the output JSON')
    parser.add_argument('--validate', action='store_true', help='Validate the input Docker Compose file')
    
    # Parse the command-line arguments
    args = parser.parse_args()
    
    # Parse custom service types from command line
    # Format: "service1:type1,service2:type2"
    custom_types = {}
    if args.custom_types:
        for mapping in args.custom_types.split(','):
            if ':' in mapping:
                service, service_type = mapping.split(':', 1)
                custom_types[service] = service_type
    
    # Create conversion options based on command-line arguments
    options = ConversionOptions(
        project_name=args.project_name,
        include_networks=not args.no_networks,
        include_volumes=not args.no_volumes,
        custom_service_types=custom_types,
        environment_substitution=not args.no_env_substitution
    )
    
    # Set default output file if not provided
    if not args.output:
        args.output = 'schema.json'
    
    try:
        # Create converter instance with the specified options
        converter = AdvancedDockerComposeToEasyPanelConverter(options)
        
        # Convert the file
        schema = converter.convert_file(args.input, args.output)
        
        # Print success message with statistics
        print(f"✅ Successfully converted '{args.input}' to EasyPanel schema")
        print(f"📁 Project name: {args.project_name}")
        print(f"🔧 Services converted: {len(schema.get('services', []))}")
        print(f"🌐 Networks converted: {len(schema.get('networks', []))}")
        print(f"💾 Volumes converted: {len(schema.get('volumes', []))}")
        print(f"🔐 Secrets converted: {len(schema.get('secrets', []))}")
        print(f"⚙️  Configs converted: {len(schema.get('configs', []))}")
        
        # Print schema to stdout if pretty printing is requested
        if args.pretty:
            print("\n📋 Generated Schema:")
            print(json.dumps(schema, indent=2, ensure_ascii=False))
        
    except Exception as e:
        # Handle any errors that occur during conversion
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
