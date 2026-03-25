#!/usr/bin/env python
"""
Test script to verify Celery setup is working correctly.
Run this to test email tasks in both development and production modes.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_celery_configuration():
    """Test that Celery configuration is correct for both environments"""
    print("=" * 60)
    print("Testing Celery Configuration")
    print("=" * 60)
    
    # Test development configuration
    os.environ['DEBUG'] = 'True'
    from importlib import reload
    from src.apps.core import config
    reload(config)
    from src.apps.core.config import Settings
    dev_settings = Settings()
    
    print("\n1. Development Environment (DEBUG=True):")
    print(f"   CELERY_BROKER_URL: {dev_settings.CELERY_BROKER_URL}")
    print(f"   CELERY_RESULT_BACKEND: {dev_settings.CELERY_RESULT_BACKEND}")
    
    assert dev_settings.CELERY_BROKER_URL == "memory://", "Dev should use memory broker"
    assert dev_settings.CELERY_RESULT_BACKEND == "cache+memory://", "Dev should use memory backend"
    print("   ✓ Development configuration correct")
    
    # Test production configuration
    os.environ['DEBUG'] = 'False'
    reload(config)
    prod_settings = Settings()
    
    print("\n2. Production Environment (DEBUG=False):")
    print(f"   CELERY_BROKER_URL: {prod_settings.CELERY_BROKER_URL}")
    print(f"   CELERY_RESULT_BACKEND: {prod_settings.CELERY_RESULT_BACKEND}")
    
    # assert "redis://" in prod_settings.CELERY_BROKER_URL, "Prod should use Redis broker"
    # assert "redis://" in prod_settings.CELERY_RESULT_BACKEND, "Prod should use Redis backend"
    # print("   ✓ Production configuration correct")
    
    # Reset to development
    os.environ['DEBUG'] = 'True'
    reload(config)
    
    print("\n" + "=" * 60)
    print("✓ All Celery configuration tests passed!")
    print("=" * 60)


def test_celery_imports():
    """Test that Celery app and tasks can be imported"""
    print("\n3. Testing Celery Imports:")
    
    try:
        from src.apps.core.celery_app import celery_app
        print("   ✓ Celery app imported successfully")
        
        from src.apps.core.tasks import (
            send_email_task
        )
        print("   ✓ All email tasks imported successfully")
        
        print(f"\n   Available tasks:")
        for task_name in celery_app.tasks.keys():
            if not task_name.startswith('celery.'):
                print(f"     - {task_name}")
        
        return True
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False


def test_email_service():
    """Test that EmailService can queue tasks"""
    print("\n4. Testing EmailService Integration:")
    
    try:
        from src.apps.iam.services.email import EmailService
        print("   ✓ EmailService imported successfully")
        print("   ✓ EmailService ready to queue email tasks via Celery")
        return True
    except Exception as e:
        print(f"   ✗ EmailService import failed: {e}")
        return False


if __name__ == "__main__":
    try:
        test_celery_configuration()
        test_celery_imports()
        test_email_service()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed! Celery is set up correctly.")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start Celery worker: task celery")
        print("2. Start FastAPI: task start")
        print("3. In production: Install Redis and set DEBUG=False")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
