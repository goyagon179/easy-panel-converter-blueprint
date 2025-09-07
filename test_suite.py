#!/usr/bin/env python3
"""
Comprehensive test suite for Docker Compose to EasyPanel converter.
Tests various Docker Compose configurations and edge cases.
"""

import json
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock yaml module
class MockYaml:
    @staticmethod
    def safe_load(f):
        # This will be overridden in individual tests
        return {}

sys.modules['yaml'] = MockYaml()

from docker_compose_to_easypanel_converter import DockerComposeToEasyPanelConverter

class TestSuite:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name, test_func):
        """Register a test function."""
        self.tests.append((name, test_func))
    
    def run_tests(self):
        """Run all registered tests."""
        print("🧪 Running Docker Compose to EasyPanel Converter Test Suite")
        print("=" * 60)
        
        for name, test_func in self.tests:
            try:
                print(f"\n🔍 Testing: {name}")
                result = test_func()
                if result:
                    print(f"✅ PASSED: {name}")
                    self.passed += 1
                else:
                    print(f"❌ FAILED: {name}")
                    self.failed += 1
            except Exception as e:
                print(f"💥 ERROR in {name}: {e}")
                self.failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        return self.failed == 0

# Create test suite
suite = TestSuite()

def test_basic_conversion():
    """Test basic Docker Compose conversion."""
    converter = DockerComposeToEasyPanelConverter("test-project")
    
    compose_data = {
        'version': '3.8',
        'services': {
            'web': {
                'image': 'nginx:alpine',
                'ports': ['8080:80'],
                'environment': {'NGINX_HOST': 'localhost'}
            }
        }
    }
    
    schema = converter.convert_data(compose_data)
    
    # Check basic structure
    assert 'services' in schema
    assert len(schema['services']) == 1
    assert schema['projectName'] == 'test-project'
    
    # Check service structure
    service = schema['services'][0]
    assert service['type'] == 'app'
    assert service['data']['serviceName'] == 'web'
    assert service['data']['source']['image'] == 'nginx:alpine'
    
    return True

def test_database_detection():
    """Test database service detection."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    test_cases = [
        ('mysql:8.0', 'mysql'),
        ('postgres:15', 'postgresql'),
        ('mongo:6', 'mongodb'),
        ('redis:7-alpine', 'redis'),
        ('nginx:alpine', 'app'),
        ('custom-app:latest', 'app')
    ]
    
    for image, expected in test_cases:
        service_config = {'image': image}
        detected = converter._determine_service_type(service_config)
        if detected != expected:
            print(f"  Expected {expected} for {image}, got {detected}")
            return False
    
    return True

def test_postgresql_conversion():
    """Test PostgreSQL database conversion."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    compose_data = {
        'services': {
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
    
    schema = converter.convert_data(compose_data)
    service = schema['services'][0]
    
    assert service['type'] == 'postgresql'
    assert service['data']['database'] == 'myapp'
    assert service['data']['user'] == 'user'
    assert service['data']['password'] == 'password'
    
    return True

def test_mysql_conversion():
    """Test MySQL database conversion."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    compose_data = {
        'services': {
            'db': {
                'image': 'mysql:8.0',
                'environment': {
                    'MYSQL_DATABASE': 'myapp',
                    'MYSQL_USER': 'user',
                    'MYSQL_PASSWORD': 'password',
                    'MYSQL_ROOT_PASSWORD': 'rootpass'
                }
            }
        }
    }
    
    schema = converter.convert_data(compose_data)
    service = schema['services'][0]
    
    assert service['type'] == 'mysql'
    assert service['data']['database'] == 'myapp'
    assert service['data']['user'] == 'user'
    assert service['data']['password'] == 'password'
    assert service['data']['rootPassword'] == 'rootpass'
    
    return True

def test_port_mapping():
    """Test port mapping conversion."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    # Test string format
    ports = converter._convert_ports(['8080:80', '3000:3000'])
    assert len(ports) == 2
    assert ports[0]['published'] == 8080
    assert ports[0]['target'] == 80
    assert ports[1]['published'] == 3000
    assert ports[1]['target'] == 3000
    
    # Test object format
    ports = converter._convert_ports([
        {'published': 8080, 'target': 80},
        {'published': 3000, 'target': 3000}
    ])
    assert len(ports) == 2
    assert ports[0]['published'] == 8080
    assert ports[0]['target'] == 80
    
    return True

def test_environment_variables():
    """Test environment variable conversion."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    # Test dict format
    env_dict = {'KEY1': 'value1', 'KEY2': 'value2'}
    result = converter._convert_environment(env_dict)
    assert result == env_dict
    
    # Test list format
    env_list = ['KEY1=value1', 'KEY2=value2']
    result = converter._convert_environment(env_list)
    assert result == {'KEY1': 'value1', 'KEY2': 'value2'}
    
    return True

def test_volume_mapping():
    """Test volume mapping conversion."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    # Test bind mount
    volumes = converter._convert_volumes(['./html:/usr/share/nginx/html'])
    assert len(volumes) == 1
    assert volumes[0]['hostPath'] == './html'
    assert volumes[0]['containerPath'] == '/usr/share/nginx/html'
    
    # Test named volume
    volumes = converter._convert_volumes(['postgres_data:/var/lib/postgresql/data'])
    assert len(volumes) == 1
    assert volumes[0]['volumeName'] == 'postgres_data'
    assert volumes[0]['containerPath'] == '/var/lib/postgresql/data'
    
    return True

def test_build_configuration():
    """Test build configuration conversion."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    compose_data = {
        'services': {
            'app': {
                'build': {
                    'context': './app',
                    'dockerfile': 'Dockerfile.prod'
                },
                'ports': ['3000:3000']
            }
        }
    }
    
    schema = converter.convert_data(compose_data)
    service = schema['services'][0]
    
    assert service['type'] == 'app'
    assert service['data']['source']['type'] == 'dockerfile'
    assert service['data']['source']['context'] == './app'
    assert service['data']['source']['dockerfile'] == 'Dockerfile.prod'
    
    return True

def test_dependencies():
    """Test service dependencies."""
    converter = DockerComposeToEasyPanelConverter("test")
    
    compose_data = {
        'services': {
            'api': {
                'image': 'node:18',
                'depends_on': ['db', 'redis']
            },
            'db': {
                'image': 'postgres:15'
            },
            'redis': {
                'image': 'redis:7'
            }
        }
    }
    
    schema = converter.convert_data(compose_data)
    api_service = next(s for s in schema['services'] if s['data']['serviceName'] == 'api')
    
    assert 'dependsOn' in api_service['data']
    assert api_service['data']['dependsOn'] == ['db', 'redis']
    
    return True

def test_complex_stack():
    """Test complex multi-service stack."""
    converter = DockerComposeToEasyPanelConverter("complex-project")
    
    compose_data = {
        'version': '3.8',
        'services': {
            'frontend': {
                'build': './frontend',
                'ports': ['3000:3000'],
                'environment': {'REACT_APP_API_URL': 'http://backend:8000'},
                'depends_on': ['backend']
            },
            'backend': {
                'image': 'python:3.11',
                'ports': ['8000:8000'],
                'environment': {
                    'DATABASE_URL': 'postgresql://user:pass@postgres:5432/db',
                    'REDIS_URL': 'redis://redis:6379'
                },
                'depends_on': ['postgres', 'redis']
            },
            'postgres': {
                'image': 'postgres:15',
                'environment': {
                    'POSTGRES_DB': 'myapp',
                    'POSTGRES_USER': 'user',
                    'POSTGRES_PASSWORD': 'password'
                }
            },
            'redis': {
                'image': 'redis:7-alpine'
            }
        }
    }
    
    schema = converter.convert_data(compose_data)
    
    # Check all services are converted
    assert len(schema['services']) == 4
    
    # Check service types
    service_types = [s['type'] for s in schema['services']]
    assert 'app' in service_types  # frontend and backend
    assert 'postgresql' in service_types  # postgres
    assert 'redis' in service_types  # redis
    
    return True

# Register all tests
suite.test("Basic Conversion", test_basic_conversion)
suite.test("Database Detection", test_database_detection)
suite.test("PostgreSQL Conversion", test_postgresql_conversion)
suite.test("MySQL Conversion", test_mysql_conversion)
suite.test("Port Mapping", test_port_mapping)
suite.test("Environment Variables", test_environment_variables)
suite.test("Volume Mapping", test_volume_mapping)
suite.test("Build Configuration", test_build_configuration)
suite.test("Dependencies", test_dependencies)
suite.test("Complex Stack", test_complex_stack)

if __name__ == "__main__":
    success = suite.run_tests()
    sys.exit(0 if success else 1)
