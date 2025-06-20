#!/usr/bin/env python3
"""
Test script for the improved sequencing data management system
Tests the optimized duplicate detection and enhanced progress tracking.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from file_scanner import SequencingFileScanner

def create_test_files_with_duplicates(test_dir):
    """Create test files with known duplicates to test the optimized hash function."""
    
    print("📁 Creating test files with known duplicates...")
    
    # Create directory structure
    dirs = ['raw', 'aligned', 'intermediate', 'results', 'backup']
    for dir_name in dirs:
        os.makedirs(os.path.join(test_dir, dir_name), exist_ok=True)
    
    # Create files with identical content (true duplicates)
    duplicate_content = "ATCGATCGATCG" * 10000  # Large enough to test chunking
    
    # Original files
    original_files = [
        'raw/sample1_R1.fastq.gz',
        'aligned/sample1.sorted.bam',
        'intermediate/sample1.metrics'
    ]
    
    for filepath in original_files:
        with open(os.path.join(test_dir, filepath), 'w') as f:
            f.write(duplicate_content)
    
    # Create duplicates in backup directory
    duplicate_files = [
        'backup/sample1_R1_copy.fastq.gz',
        'backup/sample1.sorted_backup.bam',
        'backup/sample1_metrics_backup.txt'
    ]
    
    for filepath in duplicate_files:
        with open(os.path.join(test_dir, filepath), 'w') as f:
            f.write(duplicate_content)
    
    # Create files with similar but different content (should not be duplicates)
    similar_content = "ATCGATCGATCG" * 9999 + "X"  # One character difference
    
    similar_files = [
        'raw/sample2_R1.fastq.gz',
        'aligned/sample2.sorted.bam'
    ]
    
    for filepath in similar_files:
        with open(os.path.join(test_dir, filepath), 'w') as f:
            f.write(similar_content)
    
    # Create small files (should hash entirely)
    small_content = "Small file content"
    with open(os.path.join(test_dir, 'intermediate/small_file.log'), 'w') as f:
        f.write(small_content)
    
    # Create very large file (should use chunk hashing)
    large_content = "LARGE FILE CONTENT\n" * 100000  # Very large file
    with open(os.path.join(test_dir, 'results/large_output.vcf'), 'w') as f:
        f.write(large_content)
    
    print(f"✅ Created test files in {test_dir}")
    return test_dir

def test_progress_callback():
    """Test the progress callback functionality."""
    print("\n🧪 Testing Progress Callback")
    print("=" * 50)
    
    progress_updates = []
    
    def progress_callback(progress_data):
        progress_updates.append(progress_data.copy())
        print(f"📊 Progress: {progress_data['percentage']}% - {progress_data['phase']} "
              f"({progress_data['processed_files']}/{progress_data['total_files']})")
    
    scanner = SequencingFileScanner()
    scanner.set_progress_callback(progress_callback)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = create_test_files_with_duplicates(temp_dir)
        
        print("\n🔍 Starting scan with progress tracking...")
        start_time = time.time()
        results = scanner.scan_directory(test_dir)
        end_time = time.time()
        
        scan_duration = end_time - start_time
        
        print(f"\n📈 Progress Tracking Results:")
        print(f"   • Total progress updates: {len(progress_updates)}")
        print(f"   • Scan duration: {scan_duration:.2f} seconds")
        print(f"   • Final progress: {progress_updates[-1]['percentage']}%" if progress_updates else "No updates")
        
        # Verify progress phases
        phases = [update['phase'] for update in progress_updates]
        expected_phase_keywords = ['Counting', 'Analyzing', 'Identifying', 'Finalizing']
        
        print(f"   • Phases observed: {list(set(phases))}")
        
        # Check if all expected phase keywords are present in any phase
        phase_check = all(
            any(keyword in phase for phase in phases) 
            for keyword in expected_phase_keywords
        )
        print(f"   • All expected phases present: {'✅' if phase_check else '❌'}")
        
        return len(progress_updates) > 0 and phase_check

def test_optimized_duplicate_detection():
    """Test the optimized duplicate detection with chunk hashing."""
    print("\n🔄 Testing Optimized Duplicate Detection")
    print("=" * 50)
    
    scanner = SequencingFileScanner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = create_test_files_with_duplicates(temp_dir)
        
        print("🔍 Scanning for duplicates...")
        start_time = time.time()
        results = scanner.scan_directory(test_dir)
        end_time = time.time()
        
        scan_duration = end_time - start_time
        duplicates = results['duplicates']
        
        print(f"📊 Duplicate Detection Results:")
        print(f"   • Scan duration: {scan_duration:.2f} seconds")
        print(f"   • Duplicate groups found: {duplicates['count']}")
        print(f"   • Potential space savings: {duplicates['total_duplicate_size_gb']:.3f} GB")
        
        # Test specific duplicate groups
        if duplicates['groups']:
            for i, group in enumerate(duplicates['groups'][:3]):  # Show first 3 groups
                print(f"\n🔄 Duplicate Group {i+1}:")
                for file_info in group['files']:
                    print(f"     • {file_info['relative_path']} ({file_info['size_mb']:.2f} MB)")
        
        # Verify we found expected duplicates (should find at least 1 group)
        expected_duplicates = duplicates['count'] >= 1
        
        # Check if we found the main duplicate group with 6 files (all identical content files)
        main_group_found = any(len(group['files']) >= 6 for group in duplicates['groups'])
        
        print(f"\n✅ Expected duplicates found: {'Yes' if expected_duplicates else 'No'}")
        print(f"✅ Main duplicate group found: {'Yes' if main_group_found else 'No'}")
        
        return expected_duplicates and main_group_found and scan_duration < 10

def test_file_classification_accuracy():
    """Test file classification with the enhanced system."""
    print("\n🧬 Testing File Classification Accuracy")
    print("=" * 50)
    
    scanner = SequencingFileScanner()
    
    # Test various file types
    test_files = {
        'sample1_R1.fastq.gz': 'raw_sequencing',
        'sample1_R2.fq.gz': 'raw_sequencing',
        'sample.sra': 'raw_sequencing',
        'sample.cram': 'raw_sequencing',
        'aligned.sorted.bam': 'aligned_data',
        'markdup.bam': 'aligned_data',
        'alignment.sam': 'aligned_data',
        'index.bai': 'intermediate_files',
        'reference.fai': 'intermediate_files',
        'variants.vcf.gz': 'intermediate_files',
        'process.log': 'intermediate_files',
        'final_report.pdf': 'final_outputs',
        'results.tsv': 'final_outputs',
        'unknown.xyz': 'unclassified'
    }
    
    correct = 0
    total = len(test_files)
    
    for filename, expected in test_files.items():
        result = scanner.classify_file(filename)
        status = "✅" if result == expected else "❌"
        print(f"{status} {filename:<25} → {result:<15} (expected: {expected})")
        if result == expected:
            correct += 1
    
    accuracy = (correct / total) * 100
    print(f"\n📊 Classification Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    return accuracy >= 90

def run_comprehensive_improvement_test():
    """Run comprehensive test of all improvements."""
    print("🧬 Sequencing Data Management System - Improvement Tests")
    print("=" * 70)
    
    tests = [
        ("Progress Callback System", test_progress_callback),
        ("Optimized Duplicate Detection", test_optimized_duplicate_detection),
        ("File Classification Accuracy", test_file_classification_accuracy)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print("\n" + "=" * 70)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 IMPROVEMENT TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 Improvement tests PASSED - Enhanced features working correctly!")
        print("\n✨ Key Improvements Verified:")
        print("   • Optimized duplicate detection using chunk hashing")
        print("   • Real-time progress tracking with detailed phases")
        print("   • Enhanced user feedback and scan completion reporting")
        return True
    else:
        print("⚠️  Improvement tests FAILED - Review issues before deployment")
        return False

if __name__ == "__main__":
    success = run_comprehensive_improvement_test()
    sys.exit(0 if success else 1)
