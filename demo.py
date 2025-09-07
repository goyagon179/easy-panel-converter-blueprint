#!/usr/bin/env python3
"""
Demo script for Docker Compose to EasyPanel converter.
This script demonstrates the converter's capabilities with sample data.
"""

import json
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock yaml module for demo
class MockYaml:
    @staticmethod
    def safe_load(f):
        return {
            'version': '3.8',
            'services': {
                'frontend': {
                    'build': {
                        'context': './frontend',
                        'dockerfile': 'Dockerfile.prod'
                    },
                    'ports': ['3000:3000'],
                    'environment': {
                        'REACT_APP_API_URL': 'http://backend:8000',
                        'NODE_ENV': 'production'
                    },
                    'depends_on': ['backend']
                },
                'backend': {
                    'image': 'python:3.11-slim',
                    'ports': ['8000:8000'],
                    'environment': {
                        'DATABASE_URL': 'postgresql://user:pass@postgres:5432/myapp',
                        'REDIS_URL': 'redis://redis:6379/0'
                    },
                    'volumes': ['./backend:/app'],
                    'command': ['python', 'manage.py', 'runserver', '0.0.0.0:8000'],
                    'depends_on': ['postgres', 'redis']
                },
                'postgres': {
                    'image': 'postgres:15',
                    'environment': {
                        'POSTGRES_DB': 'myapp',
                        'POSTGRES_USER': 'user',
                        'POSTGRES_PASSWORD': 'password'
                    },
                    'volumes': ['postgres_data:/var/lib/postgresql/data'],
                    'ports': ['5432:5432']
                },
                'redis': {
                    'image': 'redis:7-alpine',
                    'ports': ['6379:6379'],
                    'volumes': ['redis_data:/data'],
                    'command': ['redis-server', '--appendonly', 'yes']
                },
                'nginx': {
                    'image': 'nginx:alpine',
                    'ports': ['80:80', '443:443'],
                    'volumes': ['./nginx/nginx.conf:/etc/nginx/nginx.conf:ro'],
                    'depends_on': ['frontend', 'backend']
                }
            },
            'volumes': {
                'postgres_data': {},
                'redis_data': {}
            },
            'networks': {
                'default': {
                    'driver': 'bridge'
                }
            }
        }

sys.modules['yaml'] = MockYaml()

from docker_compose_to_easypanel_converter import DockerComposeToEasyPanelConverter

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n{title}")
    print('-' * len(title))

def demo_basic_conversion():
    """Demonstrate basic conversion functionality."""
    print_section("🚀 Docker Compose to EasyPanel Converter Demo")
    
    print("This demo shows how to convert a Docker Compose file to EasyPanel's schema.json format.")
    print("The converter supports various service types, port mappings, environment variables, and more.")
    
    # Create converter instance
    converter = DockerComposeToEasyPanelConverter("demo-project")
    
    # Sample Docker Compose data
    compose_data = {
        'version': '3.8',
        'services': {
            'web': {
                'image': 'nginx:alpine',
                'ports': ['8080:80'],
                'environment': {
                    'NGINX_HOST': 'localhost',
                    'NGINX_PORT': '80'
                },
                'volumes': ['./html:/usr/share/nginx/html'],
                'restart': 'unless-stopped'
            },
            'api': {
                'image': 'node:18-alpine',
                'ports': ['3000:3000'],
                'environment': {
                    'NODE_ENV': 'production',
                    'PORT': '3000',
                    'DATABASE_URL': 'postgresql://user:pass@postgres:5432/myapp'
                },
                'volumes': ['./api:/app'],
                'command': ['npm', 'start'],
                'depends_on': ['postgres']
            },
            'postgres': {
                'image': 'postgres:15',
                'environment': {
                    'POSTGRES_DB': 'myapp',
                    'POSTGRES_USER': 'user',
                    'POSTGRES_PASSWORD': 'password'
                },
                'volumes': ['postgres_data:/var/lib/postgresql/data'],
                'ports': ['5432:5432']
            },
            'redis': {
                'image': 'redis:7-alpine',
                'ports': ['6379:6379'],
                'volumes': ['redis_data:/data'],
                'command': ['redis-server', '--appendonly', 'yes']
            }
        },
        'volumes': {
            'postgres_data': {},
            'redis_data': {}
        }
    }
    
    print_subsection("📋 Input: Docker Compose Configuration")
    print("Services to convert:")
    for service_name, service_config in compose_data['services'].items():
        print(f"  • {service_name}: {service_config.get('image', 'build')}")
    
    # Convert the data
    print_subsection("🔄 Converting to EasyPanel Schema...")
    schema = converter.convert_data(compose_data)
    
    print_subsection("✅ Conversion Results")
    print(f"Project name: {schema['projectName']}")
    print(f"Services converted: {len(schema['services'])}")
    print(f"Volumes converted: {len(schema.get('volumes', []))}")
    
    # Show service details
    print_subsection("🔧 Service Details")
    for service in schema['services']:
        service_type = service['type']
        service_name = service['data']['serviceName']
        print(f"  • {service_name} ({service_type})")
        
        if service_type == 'app':
            source = service['data'].get('source', {})
            if 'image' in source:
                print(f"    Image: {source['image']}")
            elif 'dockerfile' in source:
                print(f"    Build: {source.get('context', '.')}/{source.get('dockerfile', 'Dockerfile')}")
        
        if 'ports' in service['data']:
            ports = service['data']['ports']
            port_str = ', '.join([f"{p['published']}:{p['target']}" for p in ports])
            print(f"    Ports: {port_str}")
        
        if service_type in ['mysql', 'postgresql', 'mongodb', 'redis']:
            db_data = service['data']
            if 'database' in db_data:
                print(f"    Database: {db_data['database']}")
            if 'user' in db_data:
                print(f"    User: {db_data['user']}")
    
    return schema

def demo_advanced_features():
    """Demonstrate advanced features."""
    print_section("🔬 Advanced Features Demo")
    
    print("The converter supports many advanced Docker Compose features:")
    print("  • Health checks")
    print("  • Resource limits")
    print("  • Logging configuration")
    print("  • Multiple networks")
    print("  • Secrets and configs")
    print("  • Environment variable substitution")
    print("  • Custom service type mapping")
    
    # Show example of advanced configuration
    advanced_compose = {
        'version': '3.8',
        'services': {
            'app': {
                'image': 'nginx:alpine',
                'ports': ['8080:80'],
                'environment': {
                    'API_URL': '${API_URL:-http://localhost:8000}',
                    'DEBUG': '${DEBUG:-false}'
                },
                'volumes': ['./html:/usr/share/nginx/html:ro'],
                'healthcheck': {
                    'test': ['CMD', 'curl', '-f', 'http://localhost/health'],
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                },
                'deploy': {
                    'resources': {
                        'limits': {
                            'cpus': '1.0',
                            'memory': '1G'
                        },
                        'reservations': {
                            'cpus': '0.5',
                            'memory': '512M'
                        }
                    }
                },
                'logging': {
                    'driver': 'json-file',
                    'options': {
                        'max-size': '10m',
                        'max-file': '3'
                    }
                }
            }
        }
    }
    
    print_subsection("📋 Advanced Configuration Example")
    print("Health check, resource limits, and logging configuration:")
    print(json.dumps(advanced_compose, indent=2))

def demo_service_type_detection():
    """Demonstrate service type detection."""
    print_section("🎯 Service Type Detection Demo")
    
    converter = DockerComposeToEasyPanelConverter("test")
    
    test_cases = [
        ('nginx:alpine', 'app'),
        ('mysql:8.0', 'mysql'),
        ('postgres:15', 'postgresql'),
        ('mongo:6', 'mongodb'),
        ('redis:7-alpine', 'redis'),
        ('traefik:v2.10', 'app'),
        ('prometheus:latest', 'app'),
        ('grafana:latest', 'app')
    ]
    
    print("The converter automatically detects service types based on Docker images:")
    print()
    
    for image, expected_type in test_cases:
        service_config = {'image': image}
        detected_type = converter._determine_service_type(service_config)
        status = "✅" if detected_type == expected_type else "❌"
        print(f"  {status} {image:<20} → {detected_type:<12} (expected: {expected_type})")

def demo_database_mapping():
    """Demonstrate database environment variable mapping."""
    print_section("🗄️  Database Environment Variable Mapping")
    
    converter = DockerComposeToEasyPanelConverter("test")
    
    # MySQL example
    mysql_config = {
        'image': 'mysql:8.0',
        'environment': {
            'MYSQL_ROOT_PASSWORD': 'rootpass',
            'MYSQL_PASSWORD': 'userpass',
            'MYSQL_DATABASE': 'myapp',
            'MYSQL_USER': 'myuser'
        }
    }
    
    print("MySQL environment variables are automatically mapped:")
    print("  MYSQL_ROOT_PASSWORD → rootPassword")
    print("  MYSQL_PASSWORD → password")
    print("  MYSQL_DATABASE → database")
    print("  MYSQL_USER → user")
    
    # Convert and show result
    schema = converter.convert_data({'services': {'db': mysql_config}})
    db_service = schema['services'][0]
    
    print(f"\nResult: {json.dumps(db_service['data'], indent=2)}")

def demo_output_schema():
    """Show the complete output schema."""
    print_section("📄 Complete Output Schema")
    
    # Use the basic conversion result
    converter = DockerComposeToEasyPanelConverter("demo-project")
    
    compose_data = {
        'version': '3.8',
        'services': {
            'web': {
                'image': 'nginx:alpine',
                'ports': ['8080:80'],
                'environment': {'NGINX_HOST': 'localhost'},
                'volumes': ['./html:/usr/share/nginx/html']
            },
            'db': {
                'image': 'postgres:15',
                'environment': {
                    'POSTGRES_DB': 'myapp',
                    'POSTGRES_USER': 'user',
                    'POSTGRES_PASSWORD': 'password'
                }
            }
        }
    }
    
    schema = converter.convert_data(compose_data)
    
    print("The complete EasyPanel schema.json format:")
    print(json.dumps(schema, indent=2, ensure_ascii=False))

def main():
    """Run the complete demo."""
    try:
        # Run all demo sections
        schema = demo_basic_conversion()
        demo_advanced_features()
        demo_service_type_detection()
        demo_database_mapping()
        demo_output_schema()
        
        print_section("🎉 Demo Complete!")
        print("The Docker Compose to EasyPanel converter is ready to use!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Convert your Docker Compose file:")
        print("     python docker-compose-to-easypanel-converter.py -i docker-compose.yml")
        print("  3. Import the generated schema.json into EasyPanel")
        print("\nFor more information, see README.md and USAGE_GUIDE.md")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
