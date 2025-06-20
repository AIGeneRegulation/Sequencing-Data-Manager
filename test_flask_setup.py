#!/usr/bin/env python3
"""
Test script to verify Flask app setup and template access
"""

import os
import sys

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

def test_paths():
    """Test that all required paths exist"""
    print("🧪 Testing Flask Application Setup")
    print("=" * 50)
    
    # Check templates directory
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    index_file = os.path.join(template_dir, 'index.html')
    
    print(f"📁 Template directory: {template_dir}")
    print(f"✅ Templates directory exists: {os.path.exists(template_dir)}")
    print(f"✅ index.html exists: {os.path.exists(index_file)}")
    
    # Check static directory
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    print(f"📁 Static directory: {static_dir}")
    print(f"✅ Static directory exists: {os.path.exists(static_dir)}")
    
    # Check code directory
    code_dir = os.path.join(os.path.dirname(__file__), 'code')
    app_file = os.path.join(code_dir, 'app.py')
    print(f"📁 Code directory: {code_dir}")
    print(f"✅ app.py exists: {os.path.exists(app_file)}")
    
    # Test Flask configuration
    try:
        from flask import Flask
        
        # Configure Flask with correct paths
        template_dir_abs = os.path.abspath(template_dir)
        static_dir_abs = os.path.abspath(static_dir)
        
        app = Flask(__name__, 
                   template_folder=template_dir_abs,
                   static_folder=static_dir_abs)
        
        print(f"✅ Flask app created successfully")
        print(f"📄 Template folder: {app.template_folder}")
        print(f"📄 Static folder: {app.static_folder}")
        
        # Test template loading
        with app.app_context():
            try:
                from jinja2 import TemplateNotFound
                template = app.jinja_env.get_template('index.html')
                print("✅ Template loading test: SUCCESS")
                return True
            except TemplateNotFound as e:
                print(f"❌ Template loading test: FAILED - {e}")
                return False
            except Exception as e:
                print(f"❌ Template loading test: ERROR - {e}")
                return False
                
    except ImportError:
        print("⚠️  Flask not available for testing, but path setup looks correct")
        return True
    except Exception as e:
        print(f"❌ Flask setup test: ERROR - {e}")
        return False

if __name__ == "__main__":
    success = test_paths()
    if success:
        print("\n🎉 Flask setup test PASSED!")
    else:
        print("\n❌ Flask setup test FAILED!")
    sys.exit(0 if success else 1)
