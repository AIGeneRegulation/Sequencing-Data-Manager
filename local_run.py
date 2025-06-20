#!/usr/bin/env python3
"""
Local development server for the Sequencing Data Management System
This script helps run the application locally without Docker for development/testing
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['flask', 'flask-cors']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Install missing dependencies"""
    print(f"📦 Installing missing packages: {', '.join(packages)}")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user'] + packages)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    data_dir = Path("sample_data")
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (data_dir / "raw").mkdir(exist_ok=True)
    (data_dir / "aligned").mkdir(exist_ok=True)
    (data_dir / "intermediate").mkdir(exist_ok=True)
    (data_dir / "results").mkdir(exist_ok=True)
    
    # Create sample files
    files = {
        "raw/sample1_R1.fastq.gz": "Sample FASTQ data (forward reads)\n" * 1000,
        "raw/sample1_R2.fastq.gz": "Sample FASTQ data (reverse reads)\n" * 1000,
        "aligned/sample1.sorted.bam": "Sample BAM alignment data\n" * 500,
        "aligned/sample1.sorted.bam.bai": "Sample BAM index data\n" * 100,
        "intermediate/sample1.metrics": "Alignment metrics data\n" * 200,
        "intermediate/processing.log": "Processing log data\n" * 300,
        "results/final_variants.vcf.gz": "VCF variant data\n" * 400,
        "results/analysis_report.html": "<html><body>Analysis Report</body></html>\n" * 100,
    }
    
    for file_path, content in files.items():
        full_path = data_dir / file_path
        with open(full_path, 'w') as f:
            f.write(content)
    
    print(f"✅ Sample data created in {data_dir}")
    return str(data_dir.absolute())

def run_flask_app():
    """Run the Flask application"""
    print("🚀 Starting Flask application...")
    
    # Add the code directory to Python path
    code_dir = os.path.join(os.path.dirname(__file__), 'code')
    sys.path.insert(0, code_dir)
    
    # Set environment variables
    os.environ['FLASK_CONFIG'] = 'development'
    os.environ['FLASK_DEBUG'] = 'true'
    
    try:
        # Import and run the app
        from code.app import app
        
        print("🌐 Web interface starting at http://localhost:5000")
        print("📁 Sample data available in ./sample_data")
        print("🛑 Press Ctrl+C to stop the server")
        
        # Start the server
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🧬 Sequencing Data Management System - Local Development Server")
    print("=" * 70)
    
    # Check and install dependencies
    missing = check_dependencies()
    if missing:
        print(f"⚠️  Missing dependencies: {', '.join(missing)}")
        if not install_dependencies(missing):
            print("❌ Cannot proceed without required dependencies")
            print("💡 Try running: pip install --user flask flask-cors")
            return False
    
    # Create sample data
    sample_data_path = create_sample_data()
    
    # Run the application
    print("\n" + "=" * 70)
    try:
        run_flask_app()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return False
    
    print("👋 Thank you for using SeqManager!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
