#!/usr/bin/env python3
"""
EasyPanel Deployment Script

This script handles the deployment of Docker Compose projects to EasyPanel
using the converted schema.json format.

Usage:
    python deploy-to-easypanel.py --schema schema.json --environment staging
"""

import argparse
import json
import os
import sys
import time
import requests
from typing import Dict, Any, Optional


class EasyPanelDeployer:
    """Handles deployment to EasyPanel via API."""
    
    def __init__(self, api_url: str, api_token: str):
        """Initialize the deployer with API credentials."""
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        })
    
    def deploy_schema(self, schema: Dict[str, Any], project_id: str, environment: str = 'staging') -> bool:
        """
        Deploy a schema to EasyPanel.
        
        Args:
            schema: The EasyPanel schema to deploy
            project_id: Target project ID in EasyPanel
            environment: Deployment environment (staging/production)
            
        Returns:
            True if deployment was successful, False otherwise
        """
        try:
            # Modify schema for environment
            modified_schema = self._prepare_schema_for_environment(schema, environment)
            
            # Deploy to EasyPanel
            print(f"🚀 Deploying to EasyPanel ({environment})...")
            print(f"📊 Project: {modified_schema['projectName']}")
            print(f"🔧 Services: {len(modified_schema.get('services', []))}")
            print(f"💾 Volumes: {len(modified_schema.get('volumes', []))}")
            print(f"🌐 Networks: {len(modified_schema.get('networks', []))}")
            
            # Make API request to deploy
            response = self.session.post(
                f'{self.api_url}/api/projects/{project_id}/schema',
                json=modified_schema
            )
            
            if response.status_code in [200, 201]:
                print("✅ Schema deployed successfully!")
                return True
            else:
                print(f"❌ Deployment failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False
    
    def _prepare_schema_for_environment(self, schema: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """
        Prepare schema for specific environment.
        
        Args:
            schema: Original schema
            environment: Target environment
            
        Returns:
            Modified schema for the environment
        """
        # Deep copy to avoid modifying original
        import copy
        modified_schema = copy.deepcopy(schema)
        
        # Update project name with environment suffix
        if environment != 'production':
            modified_schema['projectName'] = f"{schema['projectName']}-{environment}"
        
        # Update environment variables based on target environment
        for service in modified_schema.get('services', []):
            if 'data' in service and 'environment' in service['data']:
                env_vars = service['data']['environment']
                
                # Environment-specific configurations
                if environment == 'production':
                    if 'APP_ENV' in env_vars:
                        env_vars['APP_ENV'] = 'production'
                    if 'APP_DEBUG' in env_vars:
                        env_vars['APP_DEBUG'] = 'false'
                    if 'LOG_LEVEL' in env_vars:
                        env_vars['LOG_LEVEL'] = 'warning'
                elif environment == 'staging':
                    if 'APP_ENV' in env_vars:
                        env_vars['APP_ENV'] = 'staging'
                    if 'APP_DEBUG' in env_vars:
                        env_vars['APP_DEBUG'] = 'true'
                    if 'LOG_LEVEL' in env_vars:
                        env_vars['LOG_LEVEL'] = 'debug'
                
                # Add environment-specific URLs
                if 'APP_URL' in env_vars and environment != 'production':
                    app_url = env_vars['APP_URL']
                    if not f'-{environment}' in app_url:
                        # Add environment subdomain
                        if app_url.startswith('http://'):
                            env_vars['APP_URL'] = app_url.replace('http://', f'http://{environment}.')
                        elif app_url.startswith('https://'):
                            env_vars['APP_URL'] = app_url.replace('https://', f'https://{environment}.')
        
        return modified_schema
    
    def check_deployment_status(self, project_id: str) -> Dict[str, Any]:
        """
        Check the status of a deployment.
        
        Args:
            project_id: Project ID to check
            
        Returns:
            Status information
        """
        try:
            response = self.session.get(f'{self.api_url}/api/projects/{project_id}/status')
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Status check failed: {response.status_code}'}
        except Exception as e:
            return {'error': f'Status check error: {e}'}
    
    def wait_for_deployment(self, project_id: str, timeout: int = 300) -> bool:
        """
        Wait for deployment to complete.
        
        Args:
            project_id: Project ID to monitor
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if deployment completed successfully
        """
        print("⏳ Waiting for deployment to complete...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.check_deployment_status(project_id)
            
            if 'error' in status:
                print(f"❌ Status check failed: {status['error']}")
                return False
            
            # Check if all services are running
            services_status = status.get('services', {})
            all_running = all(
                service.get('status') == 'running' 
                for service in services_status.values()
            )
            
            if all_running:
                print("✅ All services are running!")
                return True
            
            print("⏳ Services still starting...")
            time.sleep(10)
        
        print("⏰ Deployment timeout reached")
        return False


def load_schema(schema_file: str) -> Dict[str, Any]:
    """Load and validate schema file."""
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        
        # Basic validation
        required_fields = ['version', 'projectName', 'services']
        for field in required_fields:
            if field not in schema:
                raise ValueError(f"Missing required field: {field}")
        
        return schema
    except Exception as e:
        print(f"❌ Error loading schema: {e}")
        sys.exit(1)


def load_environment_config(environment: str) -> Dict[str, str]:
    """Load environment-specific configuration."""
    config = {}
    
    # Load from environment variables
    env_mapping = {
        'EASYPANEL_API_URL': 'api_url',
        'EASYPANEL_API_TOKEN': 'api_token',
        f'EASYPANEL_{environment.upper()}_PROJECT_ID': 'project_id'
    }
    
    for env_var, config_key in env_mapping.items():
        value = os.environ.get(env_var)
        if value:
            config[config_key] = value
    
    # Check for required config
    required_config = ['api_url', 'api_token', 'project_id']
    missing_config = [key for key in required_config if key not in config]
    
    if missing_config:
        print(f"❌ Missing required environment variables:")
        for key in missing_config:
            env_var = [k for k, v in env_mapping.items() if v == key][0]
            print(f"   {env_var}")
        sys.exit(1)
    
    return config


def perform_health_checks(schema: Dict[str, Any], environment: str) -> bool:
    """Perform basic health checks on deployed services."""
    print("🏥 Performing health checks...")
    
    # Extract services with health check endpoints
    services_to_check = []
    
    for service in schema.get('services', []):
        service_data = service.get('data', {})
        service_name = service_data.get('serviceName', '')
        
        # Look for services with HTTP ports
        ports = service_data.get('ports', [])
        http_ports = [p for p in ports if p.get('target') in [80, 443, 8080, 3000]]
        
        if http_ports and service.get('type') == 'app':
            services_to_check.append({
                'name': service_name,
                'port': http_ports[0]['published']
            })
    
    if not services_to_check:
        print("ℹ️  No HTTP services found for health checks")
        return True
    
    # Perform health checks
    import urllib.request
    import urllib.error
    
    all_healthy = True
    for service in services_to_check:
        try:
            # Construct health check URL
            base_url = f"http://{environment}.yourdomain.com" if environment != 'production' else "http://yourdomain.com"
            health_url = f"{base_url}:{service['port']}/health"
            
            print(f"🔍 Checking {service['name']} at {health_url}")
            
            # Simple HTTP check
            response = urllib.request.urlopen(health_url, timeout=10)
            if response.status == 200:
                print(f"✅ {service['name']} is healthy")
            else:
                print(f"⚠️  {service['name']} returned status {response.status}")
                all_healthy = False
                
        except Exception as e:
            print(f"❌ Health check failed for {service['name']}: {e}")
            all_healthy = False
    
    return all_healthy


def main():
    """Main deployment script."""
    parser = argparse.ArgumentParser(description='Deploy Docker Compose to EasyPanel')
    parser.add_argument('--schema', required=True, help='Path to schema.json file')
    parser.add_argument('--environment', choices=['staging', 'production'], default='staging', help='Target environment')
    parser.add_argument('--wait', action='store_true', help='Wait for deployment to complete')
    parser.add_argument('--health-check', action='store_true', help='Perform health checks after deployment')
    parser.add_argument('--timeout', type=int, default=300, help='Deployment timeout in seconds')
    
    args = parser.parse_args()
    
    print(f"🚀 EasyPanel Deployment Script")
    print(f"📄 Schema: {args.schema}")
    print(f"🌍 Environment: {args.environment}")
    print("=" * 50)
    
    # Load schema
    schema = load_schema(args.schema)
    print(f"📋 Loaded schema: {schema['projectName']}")
    
    # Load environment configuration
    config = load_environment_config(args.environment)
    
    # Initialize deployer
    deployer = EasyPanelDeployer(config['api_url'], config['api_token'])
    
    # Deploy schema
    success = deployer.deploy_schema(schema, config['project_id'], args.environment)
    
    if not success:
        print("❌ Deployment failed!")
        sys.exit(1)
    
    # Wait for deployment if requested
    if args.wait:
        deployment_ready = deployer.wait_for_deployment(config['project_id'], args.timeout)
        if not deployment_ready:
            print("❌ Deployment did not complete successfully!")
            sys.exit(1)
    
    # Perform health checks if requested
    if args.health_check:
        healthy = perform_health_checks(schema, args.environment)
        if not healthy:
            print("⚠️  Some health checks failed!")
            sys.exit(1)
    
    print("🎉 Deployment completed successfully!")


if __name__ == '__main__':
    main()
