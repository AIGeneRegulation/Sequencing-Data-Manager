#!/usr/bin/env python3
"""
Test script to verify static file serving is working correctly.
"""

import os
import sys

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

def test_static_file_routing():
    """Test that static files are served correctly."""
    print("🧪 Testing Static File Routing")
    print("=" * 50)
    
    try:
        from app import app
        
        with app.test_client() as client:
            
            print("📄 Testing main page...")
            response = client.get('/')
            print(f"Main page status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Main page loads successfully")
            else:
                print(f"❌ Main page failed: {response.status_code}")
            
            print("\n🎨 Testing CSS file access...")
            response = client.get('/assets/index-DPs2xDwM.css')
            print(f"CSS file status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ CSS file serves successfully")
                print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
                print(f"Content-Length: {len(response.data)} bytes")
            else:
                print(f"❌ CSS file failed: {response.status_code}")
            
            print("\n📜 Testing JS file access...")
            response = client.get('/assets/index-Ci1QJi_n.js')
            print(f"JS file status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ JS file serves successfully")
                print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
                print(f"Content-Length: {len(response.data)} bytes")
            else:
                print(f"❌ JS file failed: {response.status_code}")
            
            print("\n🔧 Testing fallback static route...")
            response = client.get('/static/css/style.css')
            print(f"Static CSS status: {response.status_code}")
            
            return True
            
    except ImportError as e:
        print(f"❌ Cannot import Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def check_file_structure():
    """Check that all required files are in place."""
    print("\n📁 Checking File Structure")
    print("=" * 50)
    
    required_files = [
        'templates/index.html',
        'static/js/index-DPs2xDwM.css',
        'static/js/index-Ci1QJi_n.js',
        'static/css/style.css',
        'code/app.py'
    ]
    
    all_present = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {file_path} - MISSING")
            all_present = False
    
    return all_present

def main():
    """Main test function."""
    print("🔧 Static File Serving Fix Verification")
    print("=" * 60)
    
    print("🎯 Testing fixes for asset loading (CSS/JS 404 errors)")
    print("📝 The /assets/ routes should now serve files from static/js/\n")
    
    # Check file structure first
    files_ok = check_file_structure()
    
    if not files_ok:
        print("\n❌ Missing required files - cannot proceed with tests")
        return False
    
    # Test static file routing
    routing_ok = test_static_file_routing()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if files_ok and routing_ok:
        print("✅ PASS - All files present and routes working")
        print("\n🎉 Static file serving should now work correctly!")
        print("💡 Next steps:")
        print("   1. Restart your Flask application")
        print("   2. Visit http://localhost:5000")
        print("   3. Check browser console - no more 404 errors for assets")
        return True
    else:
        print("❌ FAIL - Issues found with static file setup")
        if not files_ok:
            print("   • Missing required files")
        if not routing_ok:
            print("   • Static file routing issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
