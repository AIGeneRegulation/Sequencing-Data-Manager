#!/usr/bin/env python3
"""
Quick start script for the Sequencing Data Management System
This ensures all components are properly set up and provides helpful guidance.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def check_file_structure():
    """Verify all required files are present."""
    print("📁 Checking File Structure...")
    
    required_files = {
        'templates/index.html': 'Main HTML template',
        'static/js/index-DPs2xDwM.css': 'Frontend CSS bundle',
        'static/js/index-Ci1QJi_n.js': 'Frontend JS bundle',
        'code/app.py': 'Flask application',
        'code/file_scanner.py': 'File scanning engine',
        'code/config.py': 'Configuration system'
    }
    
    missing_files = []
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({size:,} bytes) - {description}")
        else:
            print(f"  ❌ {file_path} - MISSING - {description}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def check_dependencies():
    """Check if required Python packages are available."""
    print("\n📦 Checking Dependencies...")
    
    required_packages = ['flask', 'flask_cors']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('_', '-').replace('-', '_'))
            print(f"  ✅ {package} - Available")
        except ImportError:
            print(f"  ❌ {package} - Missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def create_sample_data():
    """Create sample data for testing."""
    print("\n📊 Creating Sample Data...")
    
    data_dir = Path("sample_data")
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    for subdir in ['raw', 'aligned', 'intermediate', 'results']:
        (data_dir / subdir).mkdir(exist_ok=True)
    
    # Create sample files
    sample_files = {
        'raw/sample1_R1.fastq.gz': 'Sample FASTQ data (forward reads)\n' * 500,
        'raw/sample1_R2.fastq.gz': 'Sample FASTQ data (reverse reads)\n' * 500,
        'aligned/sample1.sorted.bam': 'Sample BAM alignment data\n' * 300,
        'aligned/sample1.sorted.bam.bai': 'Sample BAM index data\n' * 50,
        'intermediate/sample1.metrics': 'Alignment metrics data\n' * 100,
        'results/final_variants.vcf.gz': 'VCF variant data\n' * 200,
    }
    
    for file_path, content in sample_files.items():
        full_path = data_dir / file_path
        if not full_path.exists():
            with open(full_path, 'w') as f:
                f.write(content)
    
    print(f"  ✅ Sample data created in {data_dir.absolute()}")
    return str(data_dir.absolute())

def print_startup_instructions():
    """Print clear startup instructions."""
    print("\n" + "=" * 60)
    print("🚀 STARTUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n📋 The static file routing has been fixed!")
    print("   • /assets/ requests now route to static/js/ directory")
    print("   • CSS and JS files should load without 404 errors")
    print("   • Frontend should display properly")
    
    print("\n🔧 To start the application:")
    
    print("\n   Option 1 - Local Development (Recommended):")
    print("   ```")
    print("   python local_run.py")
    print("   ```")
    
    print("\n   Option 2 - Direct Flask Run:")
    print("   ```")
    print("   cd code")
    print("   python app.py")
    print("   ```")
    
    print("\n   Option 3 - Docker (if preferred):")
    print("   ```")
    print("   ./run.sh demo")
    print("   ```")
    
    print("\n🌐 After starting:")
    print("   1. Visit: http://localhost:5000")
    print("   2. Check browser console - should see no 404 errors")
    print("   3. Interface should load cleanly with empty dashboard")
    print("   4. Use scanner to scan: ./sample_data")
    
    print("\n🔍 Troubleshooting:")
    print("   • If still getting 404s: restart the Flask application")
    print("   • Check browser network tab for asset loading")
    print("   • Verify Flask logs show assets being served correctly")

def main():
    """Main function."""
    print("🧬 Sequencing Data Management System - Quick Start")
    print("=" * 60)
    print("🔧 Verifying setup after static file routing fix...\n")
    
    # Check file structure
    files_ok, missing_files = check_file_structure()
    
    # Check dependencies  
    deps_ok, missing_deps = check_dependencies()
    
    # Create sample data
    sample_data_path = create_sample_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SETUP VERIFICATION SUMMARY")
    print("=" * 60)
    
    if files_ok:
        print("✅ All required files present")
    else:
        print(f"❌ Missing files: {', '.join(missing_files)}")
    
    if deps_ok:
        print("✅ All dependencies available")
    else:
        print(f"⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("   💡 Will be auto-installed by local_run.py")
    
    print(f"✅ Sample data ready: {sample_data_path}")
    
    # Print instructions
    print_startup_instructions()
    
    if files_ok:
        print("\n🎉 Setup verification complete! Ready to start the application.")
        return True
    else:
        print("\n❌ Setup issues found - please check missing files")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
