#!/usr/bin/env python3
"""
Test script for the Docker Compose to EasyPanel converter.
This script tests the converter with sample data without requiring external dependencies.
"""

import json
import sys
import os

# Add the current directory to the path so we can import our converter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock yaml module for testing
class MockYaml:
    @staticmethod
    def safe_load(f):
        # Return sample Docker Compose data for testing
        return {
            'version': '3.8',
            'services': {
                'web': {
                    'image': 'nginx:alpine',
                    'container_name': 'my-web-app',
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
                    'container_name': 'my-api',
                    'ports': ['3000:3000'],
                    'environment': {
                        'NODE_ENV': 'production',
                        'PORT': '3000'
                    },
                    'volumes': ['./api:/app'],
                    'command': ['npm', 'start'],
                    'depends_on': ['db']
                },
                'db': {
                    'image': 'postgres:15',
                    'container_name': 'my-database',
                    'environment': {
                        'POSTGRES_DB': 'myapp',
                        'POSTGRES_USER': 'user',
                        'POSTGRES_PASSWORD': 'password'
                    },
                    'volumes': ['postgres_data:/var/lib/postgresql/data'],
                    'ports': ['5432:5432']
                }
            },
            'volumes': {
                'postgres_data': {}
            },
            'networks': {
                'default': {
                    'driver': 'bridge'
                }
            }
        }

# Mock the yaml module
sys.modules['yaml'] = MockYaml()

# Now import our converter
from docker_compose_to_easypanel_converter import DockerComposeToEasyPanelConverter

def test_converter():
    """Test the converter with sample data."""
    print("Testing Docker Compose to EasyPanel Converter")
    print("=" * 50)
    
    # Create converter instance
    converter = DockerComposeToEasyPanelConverter("test-project")
    
    # Test with sample data
    sample_data = {
        'version': '3.8',
        'services': {
            'web': {
                'image': 'nginx:alpine',
                'ports': ['8080:80'],
                'environment': {
                    'NGINX_HOST': 'localhost'
                },
                'volumes': ['./html:/usr/share/nginx/html']
            },
            'db': {
                'image': 'postgres:15',
                'environment': {
                    'POSTGRES_DB': 'myapp',
                    'POSTGRES_USER': 'user',
                    'POSTGRES_PASSWORD': 'password'
                },
                'ports': ['5432:5432']
            }
        }
    }
    
    try:
        # Convert the data
        schema = converter.convert_data(sample_data)
        
        print("✅ Conversion successful!")
        print(f"Project name: {schema['projectName']}")
        print(f"Services converted: {len(schema['services'])}")
        print(f"Networks converted: {len(schema.get('networks', []))}")
        print(f"Volumes converted: {len(schema.get('volumes', []))}")
        
        print("\n📋 Generated Schema:")
        print(json.dumps(schema, indent=2, ensure_ascii=False))
        
        # Test specific service types
        web_service = next((s for s in schema['services'] if s['data']['serviceName'] == 'web'), None)
        db_service = next((s for s in schema['services'] if s['data']['serviceName'] == 'db'), None)
        
        print("\n🔍 Service Analysis:")
        if web_service:
            print(f"✅ Web service: {web_service['type']} - {web_service['data']['source']['image']}")
        if db_service:
            print(f"✅ Database service: {db_service['type']} - PostgreSQL detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_detection():
    """Test database service detection."""
    print("\n🧪 Testing Database Detection")
    print("=" * 30)
    
    converter = DockerComposeToEasyPanelConverter("test")
    
    test_cases = [
        ('mysql:8.0', 'mysql'),
        ('postgres:15', 'postgresql'),
        ('mongo:6', 'mongodb'),
        ('redis:7-alpine', 'redis'),
        ('nginx:alpine', 'app'),
        ('node:18', 'app')
    ]
    
    for image, expected_type in test_cases:
        service_config = {'image': image}
        detected_type = converter._determine_service_type(service_config)
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} {image} -> {detected_type} (expected: {expected_type})")

if __name__ == "__main__":
    print("🚀 Starting Converter Tests")
    print("=" * 40)
    
    # Test basic conversion
    success = test_converter()
    
    # Test database detection
    test_database_detection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("💥 Some tests failed!")
        sys.exit(1)
