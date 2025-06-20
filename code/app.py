#!/usr/bin/env python3
"""
Flask Web Application for Sequencing Data Management
Provides REST API endpoints for the file scanning and management system.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import threading
import time
from datetime import datetime
from file_scanner import SequencingFileScanner
from config import get_config
import logging

# Configure Flask with correct paths for templates and static files
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
config = get_config()
app.config.from_object(config)
config.init_app(app)
CORS(app)

logger = logging.getLogger(__name__)

# Global variables
scanner = SequencingFileScanner()

def progress_callback(progress_data):
    """Callback function to update scan progress in real-time."""
    global scan_status
    scan_status.update({
        'phase': progress_data.get('phase', ''),
        'total_files': progress_data.get('total_files', 0),
        'processed_files': progress_data.get('processed_files', 0),
        'progress': progress_data.get('percentage', 0)
    })

# Set the progress callback for the scanner
scanner.set_progress_callback(progress_callback)

scan_status = {
    'scanning': False,
    'progress': 0,
    'current_directory': '',
    'error': None,
    'phase': '',
    'total_files': 0,
    'processed_files': 0,
    'start_time': None,
    'end_time': None
}
scan_results = {}

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start scanning a directory."""
    global scan_status, scan_results
    
    data = request.get_json()
    directory_path = data.get('directory_path', '')
    
    if not directory_path:
        return jsonify({'error': 'Directory path is required'}), 400
    
    if not os.path.exists(directory_path):
        return jsonify({'error': 'Directory does not exist'}), 400
    
    if not os.path.isdir(directory_path):
        return jsonify({'error': 'Path is not a directory'}), 400
    
    if scan_status['scanning']:
        return jsonify({'error': 'Scan already in progress'}), 409
    
    def run_scan():
        global scan_status, scan_results
        try:
            # Initialize scan status
            scan_status.update({
                'scanning': True,
                'progress': 0,
                'current_directory': directory_path,
                'error': None,
                'phase': 'Initializing...',
                'total_files': 0,
                'processed_files': 0,
                'start_time': datetime.now().isoformat(),
                'end_time': None
            })
            
            logger.info(f"🔍 Starting scan of directory: {directory_path}")
            
            # Run the scan with progress tracking
            results = scanner.scan_directory(directory_path)
            scan_results = results
            
            # Mark scan as completed
            scan_status.update({
                'scanning': False,
                'progress': 100,
                'phase': 'Completed',
                'end_time': datetime.now().isoformat()
            })
            
            logger.info("✅ Scan completed successfully")
            
        except Exception as e:
            scan_status.update({
                'scanning': False,
                'error': str(e),
                'phase': 'Error',
                'end_time': datetime.now().isoformat()
            })
            logger.error(f"❌ Scan failed: {e}")
    
    # Start scan in background thread
    thread = threading.Thread(target=run_scan)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scan started', 'status': 'scanning'})

@app.route('/api/scan/status', methods=['GET'])
def get_scan_status():
    """Get current scan status."""
    return jsonify(scan_status)

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get scan results."""
    if not scan_results:
        # Return empty results structure instead of 404
        empty_results = {
            'total_size_gb': 0,
            'categories': {
                'raw_sequencing': {'count': 0, 'total_size': 0, 'size_gb': 0, 'percentage': 0, 'files': []},
                'aligned_data': {'count': 0, 'total_size': 0, 'size_gb': 0, 'percentage': 0, 'files': []},
                'intermediate_files': {'count': 0, 'total_size': 0, 'size_gb': 0, 'percentage': 0, 'files': []},
                'final_outputs': {'count': 0, 'total_size': 0, 'size_gb': 0, 'percentage': 0, 'files': []},
                'unclassified': {'count': 0, 'total_size': 0, 'size_gb': 0, 'percentage': 0, 'files': []}
            },
            'duplicates': {
                'count': 0,
                'total_duplicate_size': 0,
                'total_duplicate_size_gb': 0,
                'groups': []
            }
        }
        return jsonify(empty_results)
    
    return jsonify(scan_results)

@app.route('/api/delete', methods=['POST'])
def delete_files():
    """Delete selected files."""
    data = request.get_json()
    file_paths = data.get('file_paths', [])
    
    if not file_paths:
        return jsonify({'error': 'No files specified for deletion'}), 400
    
    try:
        delete_results = scanner.delete_files(file_paths)
        logger.info(f"Deletion completed: {delete_results['total_deleted']} deleted, {delete_results['total_failed']} failed")
        return jsonify(delete_results)
    except Exception as e:
        logger.error(f"Deletion failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<category>', methods=['GET'])
def get_files_by_category(category):
    """Get files from a specific category."""
    if not scan_results:
        return jsonify({'error': 'No scan results available'}), 404
    
    if category not in scan_results.get('categories', {}):
        return jsonify({'error': f'Category {category} not found'}), 404
    
    category_data = scan_results['categories'][category]
    return jsonify(category_data)

@app.route('/api/duplicates', methods=['GET'])
def get_duplicates():
    """Get duplicate files information."""
    if not scan_results:
        # Return empty duplicates structure instead of 404
        empty_duplicates = {
            'count': 0,
            'total_duplicate_size': 0,
            'total_duplicate_size_gb': 0,
            'groups': []
        }
        return jsonify(empty_duplicates)
    
    duplicates_data = scan_results.get('duplicates', {
        'count': 0,
        'total_duplicate_size': 0,
        'total_duplicate_size_gb': 0,
        'groups': []
    })
    return jsonify(duplicates_data)

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get summary statistics."""
    if not scan_results:
        # Return default summary when no scan has been performed
        default_summary = {
            'total_size_gb': 0,
            'categories': {
                'raw_sequencing': {'count': 0, 'size_gb': 0, 'percentage': 0},
                'aligned_data': {'count': 0, 'size_gb': 0, 'percentage': 0},
                'intermediate_files': {'count': 0, 'size_gb': 0, 'percentage': 0},
                'final_outputs': {'count': 0, 'size_gb': 0, 'percentage': 0},
                'unclassified': {'count': 0, 'size_gb': 0, 'percentage': 0}
            },
            'duplicates': {
                'count': 0,
                'size_gb': 0
            },
            'scan_performed': False
        }
        return jsonify(default_summary)
    
    summary = {
        'total_size_gb': scan_results.get('total_size_gb', 0),
        'categories': {},
        'duplicates': {
            'count': scan_results.get('duplicates', {}).get('count', 0),
            'size_gb': scan_results.get('duplicates', {}).get('total_duplicate_size_gb', 0)
        },
        'scan_performed': True
    }
    
    # Ensure all expected categories are present
    expected_categories = ['raw_sequencing', 'aligned_data', 'intermediate_files', 'final_outputs', 'unclassified']
    
    for category in expected_categories:
        if category in scan_results.get('categories', {}):
            data = scan_results['categories'][category]
            summary['categories'][category] = {
                'count': data.get('count', 0),
                'size_gb': data.get('size_gb', 0),
                'percentage': data.get('percentage', 0)
            }
        else:
            summary['categories'][category] = {
                'count': 0,
                'size_gb': 0,
                'percentage': 0
            }
    
    return jsonify(summary)

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.route('/assets/<path:filename>')
def assets_files(filename):
    """Serve assets files (for Vite-built frontend)."""
    # Map /assets/ requests to the static/js directory where the built files are located
    static_folder_abs = os.path.abspath(app.static_folder)
    js_folder = os.path.join(static_folder_abs, 'js')
    
    # Try to serve from js folder first (where Vite assets are)
    js_file_path = os.path.join(js_folder, filename)
    if os.path.exists(js_file_path):
        return send_from_directory(js_folder, filename)
    
    # Fallback to regular static folder
    return send_from_directory(static_folder_abs, filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'scan_results_available': bool(scan_results),
        'currently_scanning': scan_status.get('scanning', False)
    })

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug information endpoint."""
    return jsonify({
        'scan_status': scan_status,
        'scan_results_keys': list(scan_results.keys()) if scan_results else [],
        'template_folder': app.template_folder,
        'static_folder': app.static_folder,
        'config': {
            'DEBUG': app.config.get('DEBUG', False),
            'FLASK_CONFIG': os.environ.get('FLASK_CONFIG', 'default')
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
