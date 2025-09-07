#!/usr/bin/env python3
"""
Docker Compose to EasyPanel Schema Converter

A comprehensive converter that transforms Docker Compose files into EasyPanel's schema.json format.
Supports various service types, port mappings, environment variables, volumes, and more.

Author: AI Assistant
Version: 1.0.0
"""

# Standard Python libraries for file handling, data processing, and command-line interface
import json          # For reading/writing JSON files (EasyPanel's format)
import yaml          # For reading YAML files (Docker Compose format)
import argparse      # For handling command-line arguments
import sys           # For system operations and error handling
import os            # For file system operations
import re            # For text pattern matching (environment variable substitution)
from typing import Dict, List, Any, Optional, Union  # Type hints for better code documentation
from pathlib import Path  # Modern Python path handling


class DockerComposeToEasyPanelConverter:
    """
    Main converter class for transforming Docker Compose files to EasyPanel schema.
    
    This class acts as the central hub that coordinates the conversion process.
    It reads Docker Compose files (YAML format) and converts them to EasyPanel's
    schema.json format (JSON format) that can be imported into EasyPanel.
    """
    
    # Database service mappings - tells us which Docker images should be treated as databases
    # This is like a lookup table: if we see "mysql" in an image name, we know it's a MySQL database
    DATABASE_IMAGES = {
        'mysql': 'mysql',           # MySQL database server
        'postgres': 'postgresql',   # PostgreSQL database server  
        'postgresql': 'postgresql', # Alternative name for PostgreSQL
        'mongo': 'mongodb',         # MongoDB database server
        'mongodb': 'mongodb',       # Alternative name for MongoDB
        'redis': 'redis',           # Redis cache/message broker
        'mariadb': 'mysql',         # MariaDB (MySQL-compatible) - treat as MySQL
        'percona': 'mysql'          # Percona (MySQL-compatible) - treat as MySQL
    }
    
    # Common database environment variables - maps Docker environment variable names to EasyPanel fields
    # Each database type has different environment variable names, so we need to map them correctly
    DB_ENV_VARS = {
        'mysql': {
            'rootPassword': ['MYSQL_ROOT_PASSWORD', 'MARIADB_ROOT_PASSWORD'],  # Root user password (camelCase for EasyPanel)
            'password': ['MYSQL_PASSWORD', 'MARIADB_PASSWORD'],                 # Regular user password
            'database': ['MYSQL_DATABASE', 'MARIADB_DATABASE'],                 # Database name
            'user': ['MYSQL_USER', 'MARIADB_USER']                              # Username
        },
        'postgresql': {
            'rootPassword': ['POSTGRES_PASSWORD'],  # PostgreSQL only has one password field
            'password': ['POSTGRES_PASSWORD'],       # Same as root password in PostgreSQL
            'database': ['POSTGRES_DB'],             # Database name
            'user': ['POSTGRES_USER']                # Username
        },
        'mongodb': {
            'rootPassword': ['MONGO_ROOT_PASSWORD', 'MONGO_INITDB_ROOT_PASSWORD'],  # Admin password
            'password': ['MONGO_PASSWORD'],                                          # User password
            'database': ['MONGO_DATABASE', 'MONGO_INITDB_DATABASE'],                # Database name
            'user': ['MONGO_USER', 'MONGO_INITDB_ROOT_USERNAME']                     # Username
        },
        'redis': {
            'password': ['REDIS_PASSWORD']  # Redis only needs a password
        }
    }
    
    def __init__(self, project_name: str = "my-project", use_placeholders: bool = False):
        """
        Initialize the converter with a project name.
        
        Args:
            project_name: The name that will be used for the EasyPanel project
            use_placeholders: If True, use placeholder values instead of environment variable templates
        """
        self.project_name = project_name  # Store the project name for use in all services
        self.use_placeholders = use_placeholders  # Whether to use placeholders for EasyPanel compatibility
        self.services = []                # List to store converted services
        self.networks = []                # List to store converted networks
        self.volumes = []                 # List to store converted volumes
        
    def _get_placeholder_value(self, field_name: str, env_var: str) -> str:
        """
        Generate placeholder values for EasyPanel compatibility.
        
        EasyPanel doesn't support environment variable templates in schema imports,
        so we need to provide placeholder values that users can update after import.
        
        Args:
            field_name: The database field name (rootPassword, password, etc.)
            env_var: The original environment variable name
            
        Returns:
            Placeholder value for the field
        """
        placeholders = {
            'rootPassword': 'CHANGE_MYSQL_ROOT_PASSWORD',
            'password': 'CHANGE_DB_PASSWORD', 
            'database': 'pterodactyl',
            'user': 'pterodactyl',
            'REDIS_PASSWORD': 'CHANGE_REDIS_PASSWORD',
            'WINGS_UUID': 'CHANGE_WINGS_UUID',
            'WINGS_TOKEN': 'CHANGE_WINGS_TOKEN',
            'WINGS_NODE_ID': '1',
            'WINGS_REMOTE': 'http://panel:80',
            'WINGS_USER': 'wings',
            'WINGS_GROUP': 'wings',
            'APP_ENV': 'production',
            'APP_DEBUG': 'false',
            'APP_URL': 'http://localhost',
            'DB_HOST': 'mysql',
            'DB_PORT': '3306',
            'DB_DATABASE': 'pterodactyl',
            'DB_USERNAME': 'pterodactyl',
            'DB_PASSWORD': 'CHANGE_DB_PASSWORD',
            'REDIS_HOST': 'redis',
            'REDIS_PORT': '6379',
            'MAIL_DRIVER': 'smtp',
            'MAIL_USERNAME': 'CHANGE_EMAIL_USERNAME',
            'MAIL_PASSWORD': 'CHANGE_EMAIL_PASSWORD',
            'MAIL_HOST': 'smtp.gmail.com',
            'MAIL_PORT': '587',
            'MAIL_FROM_ADDRESS': 'noreply@yourdomain.com',
            'MAIL_FROM_NAME': 'Pterodactyl Panel'
        }
        
        return placeholders.get(field_name, f'CHANGE_{env_var}')
        
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
        (services, networks, volumes) to EasyPanel format.
        
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
        
        # Extract version and basic info (though we don't use version much)
        version = compose_data.get('version', '3')
        
        # Process services - this is the main part of Docker Compose
        # Services are the individual applications/containers you want to run
        services_data = compose_data.get('services', {})
        for service_name, service_config in services_data.items():
            service = self._convert_service(service_name, service_config)
            if service:  # Only add if conversion was successful
                self.services.append(service)
        
        # Process networks - these define how services can communicate with each other
        networks_data = compose_data.get('networks', {})
        for network_name, network_config in networks_data.items():
            network = self._convert_network(network_name, network_config)
            if network:
                self.networks.append(network)
        
        # Process volumes - these are persistent storage for your data
        volumes_data = compose_data.get('volumes', {})
        for volume_name, volume_config in volumes_data.items():
            volume = self._convert_volume(volume_name, volume_config)
            if volume:
                self.volumes.append(volume)
        
        # Create the final schema - this is the EasyPanel format
        schema = {
            "version": "1.0",                    # Schema version
            "projectName": self.project_name,    # Project name for EasyPanel
            "services": self.services,           # List of all converted services
            "networks": self.networks,           # List of all converted networks
            "volumes": self.volumes              # List of all converted volumes
        }
        
        # Write to output file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)  # Pretty-print JSON
            print(f"Schema written to: {output_file}")
        
        return schema
    
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
        
        # Determine what type of service this is (app, database, etc.)
        service_type = self._determine_service_type(service_config)
        
        # Convert based on the service type
        if service_type in self.DATABASE_IMAGES.values():
            # This is a database service (MySQL, PostgreSQL, etc.)
            return self._convert_database_service(service_name, service_config, service_type)
        else:
            # This is a regular application service
            return self._convert_app_service(service_name, service_config)
    
    def _determine_service_type(self, service_config: Dict[str, Any]) -> str:
        """
        Determine the EasyPanel service type based on Docker Compose configuration.
        
        This method looks at the Docker image name and environment variables to figure out
        what type of service this is. For example, if the image is "mysql:8.0", we know
        it's a MySQL database.
        
        Args:
            service_config: The service configuration from Docker Compose
            
        Returns:
            The service type as a string (e.g., "mysql", "postgresql", "app")
        """
        image = service_config.get('image', '')
        
        # Check for explicit database type override
        # Sometimes you want to force a service to be treated as a specific type
        env_vars = service_config.get('environment', {})
        if isinstance(env_vars, dict) and 'EASYPANEL_DATABASE' in env_vars:
            return env_vars['EASYPANEL_DATABASE']
        
        # Check image name for database types
        # Look through our database mapping to see if this image matches any known databases
        for db_image, db_type in self.DATABASE_IMAGES.items():
            if db_image in image.lower():  # Case-insensitive matching
                return db_type
        
        # Default to app type if we can't determine what it is
        return 'app'
    
    def _convert_app_service(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a service to EasyPanel app format.
        
        This handles regular application services (web servers, APIs, microservices, etc.)
        that aren't databases. It converts all the common Docker Compose settings
        like ports, environment variables, volumes, etc.
        
        Args:
            service_name: Name of the service
            service_config: Docker Compose service configuration
            
        Returns:
            Service converted to EasyPanel app format
        """
        # Start with basic service information
        service_data = {
            "projectName": self.project_name,
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
                # Detailed build configuration
                service_data["source"] = {
                    "type": "dockerfile",
                    "dockerfile": build_config.get('dockerfile', 'Dockerfile'),
                    "context": build_config.get('context', '.')
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
        
        # Return the service in EasyPanel format
        return {
            "type": "app",
            "data": service_data
        }
    
    def _convert_database_service(self, service_name: str, service_config: Dict[str, Any], db_type: str) -> Dict[str, Any]:
        """
        Convert a service to EasyPanel database format.
        
        Database services need special handling because they have specific configuration
        fields (like database name, username, password) that are different from regular apps.
        
        Args:
            service_name: Name of the database service
            service_config: Docker Compose service configuration
            db_type: Type of database (mysql, postgresql, etc.)
            
        Returns:
            Service converted to EasyPanel database format
        """
        # Start with basic service information
        service_data = {
            "projectName": self.project_name,
            "serviceName": service_name
        }
        
        # Extract database-specific environment variables
        # Convert list format to dictionary if needed
        env_vars = service_config.get('environment', {})
        if isinstance(env_vars, list):
            # Convert ["KEY=value", "KEY2=value2"] to {"KEY": "value", "KEY2": "value2"}
            env_vars = {item.split('=')[0]: item.split('=')[1] for item in env_vars if '=' in item}
        
        # Map environment variables to database fields
        # Each database type has different environment variable names
        db_env_mapping = self.DB_ENV_VARS.get(db_type, {})
        for field, env_keys in db_env_mapping.items():
            # Try each possible environment variable name for this field
            found_value = False
            for env_key in env_keys:
                if env_key in env_vars:
                    if self.use_placeholders:
                        # Use placeholder value for EasyPanel compatibility
                        # For Redis password, use the specific Redis placeholder
                        if db_type == 'redis' and field == 'password':
                            service_data[field] = self._get_placeholder_value('REDIS_PASSWORD', env_key)
                        else:
                            service_data[field] = self._get_placeholder_value(field, env_key)
                    else:
                        # Use the actual environment variable value
                        service_data[field] = env_vars[env_key]
                    found_value = True
                    break  # Found it, move to next field
            
            # If no environment variable found but we're using placeholders, provide a default
            if not found_value and self.use_placeholders:
                # For Redis password, use the REDIS_PASSWORD placeholder
                if db_type == 'redis' and field == 'password':
                    service_data[field] = self._get_placeholder_value('REDIS_PASSWORD', 'REDIS_PASSWORD')
                else:
                    service_data[field] = self._get_placeholder_value(field, env_keys[0] if env_keys else field)
        
        # Handle ports for database (usually for external access)
        ports = self._convert_ports(service_config.get('ports', []))
        if ports:
            service_data["ports"] = ports
        
        # Handle volumes for database (for data persistence)
        volumes = self._convert_volumes(service_config.get('volumes', []))
        if volumes:
            service_data["volumes"] = volumes
        
        # Handle restart policy
        if 'restart' in service_config:
            service_data["restart"] = service_config['restart']
        
        # Return the database service in EasyPanel format
        return {
            "type": db_type,
            "data": service_data
        }
    
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
                    "target": port.get('target', port.get('container', 0))
                })
        
        return converted_ports
    
    def _convert_environment(self, env_config: Union[Dict[str, str], List[str]]) -> Dict[str, str]:
        """
        Convert Docker Compose environment variables to EasyPanel format.
        
        Environment variables can be specified in two ways in Docker Compose:
        - Dictionary: {"KEY": "value", "KEY2": "value2"}
        - List: ["KEY=value", "KEY2=value2"]
        
        This method converts both to a consistent dictionary format.
        When use_placeholders is enabled, it replaces values with EasyPanel-compatible placeholders.
        
        Args:
            env_config: Environment configuration from Docker Compose
            
        Returns:
            Dictionary of environment variables
        """
        env_dict = {}
        
        if isinstance(env_config, dict):
            # Already in dictionary format
            env_dict = env_config.copy()
        elif isinstance(env_config, list):
            # Convert list format to dictionary
            for item in env_config:
                if '=' in item:
                    key, value = item.split('=', 1)  # Split on first '=' only
                    env_dict[key] = value
        
        # If using placeholders, replace values with placeholders
        if self.use_placeholders:
            for key, value in env_dict.items():
                env_dict[key] = self._get_placeholder_value(key, key)
        
        return env_dict
    
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
                    # Format: "source:container_path" - could be host path or volume name
                    source, container_path = volume.split(':', 1)
                    
                    # Check if source is a host path (starts with . / or ~) or absolute path
                    if source.startswith(('./', '/', '~', '.\\', '\\')):
                        # This is a bind mount (host path)
                        converted_volumes.append({
                            "hostPath": source,           # Path on the host machine
                            "containerPath": container_path  # Path inside the container
                        })
                    else:
                        # This is a named volume
                        converted_volumes.append({
                            "volumeName": source,         # Name of the Docker volume
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


def main():
    """
    Main CLI entry point.
    
    This function handles command-line arguments and orchestrates the conversion process.
    It's what gets called when you run the script from the command line.
    """
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(
        description="Convert Docker Compose files to EasyPanel schema.json format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i docker-compose.yml -o schema.json
  %(prog)s -i docker-compose.yml -p my-awesome-project
  %(prog)s -i docker-compose.yml -o schema.json -p my-project --pretty
        """
    )
    
    # Define command-line arguments
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input Docker Compose file path'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output schema.json file path (default: schema.json)'
    )
    
    parser.add_argument(
        '-p', '--project-name',
        default='my-project',
        help='Project name for EasyPanel (default: my-project)'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty print the output JSON'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate the input Docker Compose file before conversion'
    )
    
    parser.add_argument(
        '--easypanel-compatible',
        action='store_true',
        help='Generate EasyPanel-compatible schema with placeholder values instead of environment variable templates'
    )
    
    # Parse the command-line arguments
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Set default output file if not provided
    if not args.output:
        args.output = 'schema.json'
    
    try:
        # Create converter instance with the specified project name and options
        converter = DockerComposeToEasyPanelConverter(args.project_name, args.easypanel_compatible)
        
        # Convert the file
        schema = converter.convert_file(args.input, args.output)
        
        # Print success message with statistics
        print(f"Successfully converted '{args.input}' to EasyPanel schema")
        print(f"Project name: {args.project_name}")
        print(f"Services converted: {len(schema.get('services', []))}")
        print(f"Networks converted: {len(schema.get('networks', []))}")
        print(f"Volumes converted: {len(schema.get('volumes', []))}")
        
        # Print schema to stdout if pretty printing is requested
        if args.pretty or not args.output:
            print("\nGenerated Schema:")
            print(json.dumps(schema, indent=2, ensure_ascii=False))
        
    except Exception as e:
        # Handle any errors that occur during conversion
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# This is the entry point when the script is run directly
if __name__ == "__main__":
    main()