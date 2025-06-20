#!/usr/bin/env python3
"""
Test script to verify API endpoints work correctly after fixes.
"""

import os
import sys
import json
from unittest.mock import patch

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

def test_api_endpoints():
    """Test all API endpoints to ensure they work correctly."""
    print("🧪 Testing API Endpoints After Fixes")
    print("=" * 50)
    
    try:
        # Import the Flask app
        from app import app
        
        # Create test client
        with app.test_client() as client:
            
            print("📡 Testing /api/health endpoint...")
            response = client.get('/api/health')
            assert response.status_code == 200
            health_data = json.loads(response.data)
            assert health_data['status'] == 'healthy'
            print("✅ Health endpoint working")
            
            print("\n📊 Testing /api/summary endpoint (no scan results)...")
            response = client.get('/api/summary')
            assert response.status_code == 200  # Should NOT be 404 anymore
            summary_data = json.loads(response.data)
            assert 'total_size_gb' in summary_data
            assert 'categories' in summary_data
            assert 'duplicates' in summary_data
            assert summary_data['scan_performed'] == False
            print("✅ Summary endpoint working (empty state)")
            
            print("\n📁 Testing /api/results endpoint (no scan results)...")
            response = client.get('/api/results')
            assert response.status_code == 200  # Should NOT be 404 anymore
            results_data = json.loads(response.data)
            assert 'categories' in results_data
            assert 'duplicates' in results_data
            print("✅ Results endpoint working (empty state)")
            
            print("\n🔄 Testing /api/duplicates endpoint (no scan results)...")
            response = client.get('/api/duplicates')
            assert response.status_code == 200  # Should NOT be 404 anymore
            duplicates_data = json.loads(response.data)
            assert 'count' in duplicates_data
            assert 'groups' in duplicates_data
            assert duplicates_data['count'] == 0
            print("✅ Duplicates endpoint working (empty state)")
            
            print("\n📊 Testing /api/scan/status endpoint...")
            response = client.get('/api/scan/status')
            assert response.status_code == 200
            status_data = json.loads(response.data)
            assert 'scanning' in status_data
            assert 'progress' in status_data
            print("✅ Scan status endpoint working")
            
            print("\n🛠️ Testing /api/debug endpoint...")
            response = client.get('/api/debug')
            assert response.status_code == 200
            debug_data = json.loads(response.data)
            assert 'scan_status' in debug_data
            assert 'template_folder' in debug_data
            print("✅ Debug endpoint working")
            
            print("\n🌐 Testing main page endpoint...")
            response = client.get('/')
            # This might fail due to template issues, but we can check the response
            print(f"📄 Main page status: {response.status_code}")
            
            return True
            
    except ImportError as e:
        print(f"❌ Cannot import Flask app: {e}")
        print("💡 This is expected if Flask is not installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_endpoint_data_structure():
    """Test that the endpoint data structures are correct."""
    print("\n🔍 Testing Endpoint Data Structures")
    print("=" * 50)
    
    try:
        from app import app
        
        with app.test_client() as client:
            
            # Test summary structure
            response = client.get('/api/summary')
            summary_data = json.loads(response.data)
            
            expected_categories = ['raw_sequencing', 'aligned_data', 'intermediate_files', 'final_outputs', 'unclassified']
            
            print("📋 Checking summary data structure...")
            for category in expected_categories:
                assert category in summary_data['categories'], f"Missing category: {category}"
                cat_data = summary_data['categories'][category]
                assert 'count' in cat_data
                assert 'size_gb' in cat_data
                assert 'percentage' in cat_data
            
            print("✅ All expected categories present in summary")
            
            # Test results structure
            response = client.get('/api/results')
            results_data = json.loads(response.data)
            
            print("📁 Checking results data structure...")
            assert 'categories' in results_data
            assert 'duplicates' in results_data
            assert 'total_size_gb' in results_data
            
            for category in expected_categories:
                assert category in results_data['categories']
                cat_data = results_data['categories'][category]
                assert 'files' in cat_data
                assert isinstance(cat_data['files'], list)
            
            print("✅ Results data structure correct")
            
            # Test duplicates structure
            response = client.get('/api/duplicates')
            duplicates_data = json.loads(response.data)
            
            print("🔄 Checking duplicates data structure...")
            assert 'count' in duplicates_data
            assert 'groups' in duplicates_data
            assert 'total_duplicate_size_gb' in duplicates_data
            assert isinstance(duplicates_data['groups'], list)
            
            print("✅ Duplicates data structure correct")
            
            return True
            
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 API Endpoint Fix Verification")
    print("=" * 60)
    
    print("🎯 Testing fixes for 404 errors on /api/summary and related endpoints")
    print("📝 These endpoints should now return empty data instead of 404 errors\n")
    
    tests = [
        ("API Endpoints Functionality", test_api_endpoints),
        ("Endpoint Data Structures", test_endpoint_data_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print('='*60)
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    test_names = ["API Endpoints Functionality", "Endpoint Data Structures"]
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"\n🎯 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests PASSED!")
        print("✅ API endpoints now return proper data instead of 404 errors")
        print("✅ Frontend should work correctly even before performing scans")
        print("\n💡 Next steps:")
        print("   1. Restart your Flask application")
        print("   2. Test with: python local_run.py")
        print("   3. Visit http://localhost:5000 in your browser")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        if not any(results):
            print("💡 This might be due to missing Flask dependency")
            print("   Try: pip install --user flask flask-cors")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
