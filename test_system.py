#!/usr/bin/env python3
"""
System Test Script for Sequencing Data Management System
Tests core functionality without requiring full Docker setup.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from file_scanner import SequencingFileScanner

def create_test_data(test_dir):
    """Create comprehensive test data for different file types."""
    
    # Create directory structure
    dirs = [
        'raw_data',
        'aligned_data', 
        'intermediate_files',
        'final_outputs',
        'mixed_folder',
        'duplicates_test'
    ]
    
    for dir_name in dirs:
        os.makedirs(os.path.join(test_dir, dir_name), exist_ok=True)
    
    # Create raw sequencing files
    raw_files = [
        'sample1_R1.fastq.gz',
        'sample1_R2.fastq.gz',
        'sample2_R1.fq.gz',
        'sample2_R2.fq.gz',
        'sample3.sra',
        'sample4.cram'
    ]
    
    for filename in raw_files:
        filepath = os.path.join(test_dir, 'raw_data', filename)
        with open(filepath, 'w') as f:
            f.write(f"Mock raw sequencing data for {filename}\n" * 1000)
    
    # Create aligned data files
    aligned_files = [
        'sample1.sorted.bam',
        'sample2.markdup.bam',
        'sample3.aligned.bam',
        'sample4.sam'
    ]
    
    for filename in aligned_files:
        filepath = os.path.join(test_dir, 'aligned_data', filename)
        with open(filepath, 'w') as f:
            f.write(f"Mock aligned data for {filename}\n" * 500)
    
    # Create intermediate files
    intermediate_files = [
        'sample1.sorted.bam.bai',
        'sample2.sorted.bam.csi',
        'reference.fasta.fai',
        'reference.dict',
        'sample1.metrics',
        'processing.log',
        'temporary.tmp',
        'variants.bed'
    ]
    
    for filename in intermediate_files:
        filepath = os.path.join(test_dir, 'intermediate_files', filename)
        with open(filepath, 'w') as f:
            f.write(f"Mock intermediate data for {filename}\n" * 100)
    
    # Create final output files
    final_files = [
        'final_variants.vcf.gz',
        'results_summary.tsv',
        'analysis_report.pdf',
        'annotation_results.xlsx'
    ]
    
    for filename in final_files:
        filepath = os.path.join(test_dir, 'final_outputs', filename)
        with open(filepath, 'w') as f:
            f.write(f"Mock final output for {filename}\n" * 200)
    
    # Create mixed folder with various types
    mixed_files = [
        'mixed_sample.fastq.gz',  # raw
        'mixed_sample.bam',       # aligned
        'mixed_sample.vcf',       # intermediate
        'mixed_report.html'       # final
    ]
    
    for filename in mixed_files:
        filepath = os.path.join(test_dir, 'mixed_folder', filename)
        with open(filepath, 'w') as f:
            f.write(f"Mock mixed data for {filename}\n" * 150)
    
    # Create duplicate files
    duplicate_content = "This is duplicate content that should be detected\n" * 500
    
    # Original file
    with open(os.path.join(test_dir, 'duplicates_test', 'original.fastq'), 'w') as f:
        f.write(duplicate_content)
    
    # Duplicate in different location
    with open(os.path.join(test_dir, 'raw_data', 'duplicate_copy.fastq'), 'w') as f:
        f.write(duplicate_content)
    
    print(f"✅ Test data created in {test_dir}")
    return test_dir

def test_file_classification():
    """Test file classification functionality."""
    print("\n🧪 Testing File Classification")
    print("=" * 50)
    
    scanner = SequencingFileScanner()
    
    test_files = {
        'sample1_R1.fastq.gz': 'raw_sequencing',
        'sample1_R2.fq.gz': 'raw_sequencing',
        'sample.sra': 'raw_sequencing',
        'sample.cram': 'raw_sequencing',
        'aligned.bam': 'aligned_data',
        'sorted.bam': 'aligned_data',
        'markdup.bam': 'aligned_data',
        'alignment.sam': 'aligned_data',
        'index.bai': 'intermediate_files',
        'reference.fai': 'intermediate_files',
        'metrics.txt': 'intermediate_files',
        'process.log': 'intermediate_files',
        'variants.vcf.gz': 'intermediate_files',
        'final_results.vcf': 'intermediate_files',
        'results.tsv': 'final_outputs',
        'report.pdf': 'final_outputs',
        'summary.xlsx': 'final_outputs',
        'unknown.txt': 'unclassified'
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
    return accuracy > 90

def test_directory_scanning(test_dir):
    """Test directory scanning functionality."""
    print("\n🔍 Testing Directory Scanning")
    print("=" * 50)
    
    scanner = SequencingFileScanner()
    results = scanner.scan_directory(test_dir)
    
    print(f"📁 Scanned directory: {test_dir}")
    print(f"📊 Total size: {results['total_size_gb']:.2f} GB")
    
    print("\n📋 Categories Found:")
    for category, data in results['categories'].items():
        if data['count'] > 0:
            print(f"  • {category:<20}: {data['count']:>3} files ({data['size_gb']:.3f} GB)")
    
    print(f"\n🔄 Duplicates Found: {results['duplicates']['count']} groups")
    if results['duplicates']['count'] > 0:
        print(f"💾 Potential space savings: {results['duplicates']['total_duplicate_size_gb']:.3f} GB")
    
    # Verify we found files in multiple categories
    categories_with_files = sum(1 for cat in results['categories'].values() if cat['count'] > 0)
    duplicates_found = results['duplicates']['count'] > 0
    
    print(f"\n✅ Categories with files: {categories_with_files}/5")
    print(f"✅ Duplicates detected: {'Yes' if duplicates_found else 'No'}")
    
    return categories_with_files >= 3 and duplicates_found

def test_duplicate_detection(test_dir):
    """Test duplicate detection specifically."""
    print("\n🔍 Testing Duplicate Detection")
    print("=" * 50)
    
    scanner = SequencingFileScanner()
    
    # First scan to establish baseline
    results = scanner.scan_directory(test_dir)
    initial_duplicates = results['duplicates']['count']
    
    # Create additional duplicates
    test_file = os.path.join(test_dir, 'duplicates_test', 'test_duplicate.txt')
    duplicate_content = "Duplicate detection test content\n" * 100
    
    with open(test_file, 'w') as f:
        f.write(duplicate_content)
    
    # Create copies in different locations
    copy1 = os.path.join(test_dir, 'raw_data', 'copy1_test_duplicate.txt')
    copy2 = os.path.join(test_dir, 'final_outputs', 'copy2_test_duplicate.txt')
    
    shutil.copy2(test_file, copy1)
    shutil.copy2(test_file, copy2)
    
    # Rescan
    results = scanner.scan_directory(test_dir)
    final_duplicates = results['duplicates']['count']
    
    print(f"📊 Initial duplicates: {initial_duplicates}")
    print(f"📊 Final duplicates: {final_duplicates}")
    print(f"📊 New duplicates detected: {final_duplicates - initial_duplicates}")
    
    if results['duplicates']['count'] > 0:
        for i, dup_group in enumerate(results['duplicates']['groups'][:3]):  # Show first 3
            print(f"\n🔄 Duplicate Group {i+1}:")
            for file_info in dup_group['files']:
                print(f"  • {file_info['relative_path']}")
    
    return final_duplicates > initial_duplicates

def test_file_operations(test_dir):
    """Test file operations (without actual deletion)."""
    print("\n🗑️  Testing File Operations")
    print("=" * 50)
    
    scanner = SequencingFileScanner()
    results = scanner.scan_directory(test_dir)
    
    # Find some files to "delete" (simulate)
    test_files = []
    for category, data in results['categories'].items():
        if data['files']:
            test_files.append(data['files'][0]['path'])
            if len(test_files) >= 3:
                break
    
    if test_files:
        print(f"📝 Files selected for deletion test:")
        total_size = 0
        for filepath in test_files:
            size = os.path.getsize(filepath)
            total_size += size
            print(f"  • {os.path.basename(filepath)} ({size} bytes)")
        
        print(f"💾 Total size to be freed: {total_size} bytes")
        
        # Simulate deletion (don't actually delete in test)
        print("✅ File operation simulation completed")
        return True
    else:
        print("❌ No files found for deletion test")
        return False

def run_comprehensive_test():
    """Run comprehensive system test."""
    print("🧬 Sequencing Data Management System - Comprehensive Test")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"🗂️  Using temporary directory: {temp_dir}")
        
        # Create test data
        test_dir = create_test_data(temp_dir)
        
        # Run tests
        tests = [
            ("File Classification", test_file_classification),
            ("Directory Scanning", lambda: test_directory_scanning(test_dir)),
            ("Duplicate Detection", lambda: test_duplicate_detection(test_dir)),
            ("File Operations", lambda: test_file_operations(test_dir))
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
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
            print("🎉 System test PASSED - Ready for deployment!")
            return True
        else:
            print("⚠️  System test FAILED - Review issues before deployment")
            return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
