#!/usr/bin/env python3
"""
Sequencing Data File Scanner and Classifier
Scans directories for sequencing-related files and classifies them by type.
"""

import os
import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import re

class SequencingFileScanner:
    """Main class for scanning and classifying sequencing data files."""
    
    def __init__(self):
        self.file_patterns = {
            'raw_sequencing': {
                'extensions': ['.fastq', '.fq', '.fastq.gz', '.fq.gz', '.sra', '.cram'],
                'patterns': [
                    r'.*\.f(ast)?q(\.gz)?$',
                    r'.*\.sra$',
                    r'.*\.cram$',
                    r'.*_R[12]_.*\.f(ast)?q(\.gz)?$',  # Paired-end reads
                ]
            },
            'aligned_data': {
                'extensions': ['.bam', '.sam', '.sorted.bam', '.markdup.bam'],
                'patterns': [
                    r'.*\.bam$',
                    r'.*\.sam$',
                    r'.*sorted.*\.bam$',
                    r'.*markdup.*\.bam$',
                    r'.*aligned.*\.bam$',
                ]
            },
            'intermediate_files': {
                'extensions': ['.bai', '.csi', '.fai', '.dict', '.idx', '.bed', '.vcf.gz', '.vcf', '.gvcf', '.gvcf.gz'],
                'patterns': [
                    r'.*\.bai$',
                    r'.*\.csi$',
                    r'.*\.fai$',
                    r'.*\.dict$',
                    r'.*\.idx$',
                    r'.*\.bed$',
                    r'.*\.vcf(\.gz)?$',
                    r'.*\.gvcf(\.gz)?$',
                    r'.*\.metrics$',
                    r'.*\.log$',
                    r'.*\.tmp$',
                ]
            },
            'final_outputs': {
                'extensions': ['.vcf.gz', '.vcf', '.tsv', '.csv', '.xlsx', '.pdf', '.html'],
                'patterns': [
                    r'.*final.*\.vcf(\.gz)?$',
                    r'.*report.*\.(pdf|html)$',
                    r'.*summary.*\.(tsv|csv|xlsx)$',
                    r'.*results.*\.(tsv|csv|xlsx)$',
                    r'.*annotation.*\.(tsv|csv|xlsx)$',
                ]
            }
        }
        
        self.scan_results = {
            'raw_sequencing': [],
            'aligned_data': [],
            'intermediate_files': [],
            'final_outputs': [],
            'unclassified': []
        }
        
        self.file_sizes = {
            'raw_sequencing': 0,
            'aligned_data': 0,
            'intermediate_files': 0,
            'final_outputs': 0,
            'unclassified': 0
        }
        
        self.duplicates = []
        self.file_hashes = {}
        
        # Progress tracking
        self.progress_callback = None
        self.current_phase = ""
        self.total_files = 0
        self.processed_files = 0
    
    def set_progress_callback(self, callback):
        """Set callback function for progress updates."""
        self.progress_callback = callback
    
    def update_progress(self, phase: str = None, files_processed: int = None):
        """Update progress and call callback if set."""
        if phase:
            self.current_phase = phase
        if files_processed is not None:
            self.processed_files = files_processed
            
        if self.progress_callback:
            progress_data = {
                'phase': self.current_phase,
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'percentage': round((self.processed_files / max(self.total_files, 1)) * 100, 1)
            }
            self.progress_callback(progress_data)
    
    def get_file_hash(self, filepath: str, chunk_size: int = 65536) -> str:
        """Calculate MD5 hash using first and last chunks for efficient duplicate detection."""
        hasher = hashlib.md5()
        try:
            file_size = os.path.getsize(filepath)
            
            # Include file size in hash to distinguish files of different sizes
            hasher.update(str(file_size).encode())
            
            with open(filepath, 'rb') as f:
                if file_size <= chunk_size * 2:
                    # For small files, hash the entire content
                    while chunk := f.read(chunk_size):
                        hasher.update(chunk)
                else:
                    # For larger files, hash first and last chunks only
                    # Hash first chunk
                    first_chunk = f.read(chunk_size)
                    hasher.update(first_chunk)
                    
                    # Hash middle position (for additional uniqueness)
                    middle_pos = file_size // 2
                    f.seek(middle_pos)
                    middle_chunk = f.read(min(chunk_size, file_size - middle_pos))
                    hasher.update(middle_chunk)
                    
                    # Hash last chunk
                    if file_size > chunk_size:
                        f.seek(-chunk_size, 2)
                        last_chunk = f.read(chunk_size)
                        hasher.update(last_chunk)
                        
        except (IOError, OSError, ValueError):
            return None
        return hasher.hexdigest()
    
    def classify_file(self, filepath: str) -> str:
        """Classify a file based on its name and extension."""
        filename = os.path.basename(filepath).lower()
        
        # Check each category in priority order
        for category, patterns in self.file_patterns.items():
            # Check extensions
            for ext in patterns['extensions']:
                if filename.endswith(ext.lower()):
                    return category
            
            # Check regex patterns
            for pattern in patterns['patterns']:
                if re.match(pattern, filename, re.IGNORECASE):
                    return category
        
        return 'unclassified'
    
    def scan_directory(self, root_path: str) -> Dict:
        """Scan directory recursively for sequencing files with progress tracking."""
        print(f"🔍 Starting scan of directory: {root_path}")
        
        # Reset results
        for category in self.scan_results:
            self.scan_results[category] = []
            self.file_sizes[category] = 0
        
        self.duplicates = []
        self.file_hashes = {}
        hash_to_files = defaultdict(list)
        
        # Phase 1: Count total files
        self.update_progress("Counting files...")
        self.total_files = 0
        self.processed_files = 0
        
        print("📊 Counting files...")
        for root, dirs, files in os.walk(root_path):
            self.total_files += len(files)
        
        print(f"📈 Found {self.total_files} files to process")
        
        # Phase 2: Classify and analyze files
        self.update_progress("Analyzing files...")
        print("🔬 Analyzing and classifying files...")
        
        for root, dirs, files in os.walk(root_path):
            for file in files:
                self.processed_files += 1
                
                # Update progress every 10 files or every 5% of total
                update_interval = max(10, self.total_files // 20)
                if self.processed_files % update_interval == 0 or self.processed_files == self.total_files:
                    self.update_progress("Analyzing files...")
                    print(f"📋 Processed {self.processed_files}/{self.total_files} files ({(self.processed_files/self.total_files*100):.1f}%)")
                
                filepath = os.path.join(root, file)
                
                try:
                    file_size = os.path.getsize(filepath)
                    relative_path = os.path.relpath(filepath, root_path)
                    
                    # Classify file
                    category = self.classify_file(filepath)
                    
                    file_info = {
                        'name': file,
                        'path': filepath,
                        'relative_path': relative_path,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'directory': root
                    }
                    
                    # Add to appropriate category
                    self.scan_results[category].append(file_info)
                    self.file_sizes[category] += file_size
                    
                    # Calculate hash for duplicate detection (skip very small files)
                    if file_size > 1024:  # Skip files smaller than 1KB
                        file_hash = self.get_file_hash(filepath)
                        if file_hash:
                            self.file_hashes[filepath] = file_hash
                            hash_to_files[file_hash].append(file_info)
                
                except (OSError, IOError) as e:
                    print(f"⚠️  Error processing file {filepath}: {e}")
                    continue
        
        # Phase 3: Identify duplicates
        self.update_progress("Identifying duplicates...")
        print("🔄 Identifying duplicate files...")
        
        duplicate_count = 0
        for file_hash, files in hash_to_files.items():
            if len(files) > 1:
                duplicate_group = {
                    'hash': file_hash,
                    'files': files,
                    'total_size': sum(f['size'] for f in files),
                    'duplicate_size': sum(f['size'] for f in files[1:])  # Size of duplicates (excluding first)
                }
                self.duplicates.append(duplicate_group)
                duplicate_count += len(files) - 1  # Count duplicate files (excluding originals)
        
        # Phase 4: Final processing
        self.update_progress("Finalizing results...")
        print("📊 Finalizing results...")
        
        # Sort files by size (largest first) in each category
        for category in self.scan_results:
            self.scan_results[category].sort(key=lambda x: x['size'], reverse=True)
        
        # Sort duplicates by duplicate size
        self.duplicates.sort(key=lambda x: x['duplicate_size'], reverse=True)
        
        # Final summary
        categories_with_files = sum(1 for cat in self.scan_results.values() if len(cat) > 0)
        total_size_gb = sum(self.file_sizes.values()) / (1024**3)
        
        print(f"✅ Scan completed successfully!")
        print(f"📈 Results:")
        print(f"   • Total files processed: {self.processed_files}")
        print(f"   • Categories with files: {categories_with_files}/5")
        print(f"   • Duplicate groups found: {len(self.duplicates)}")
        print(f"   • Total data size: {total_size_gb:.2f} GB")
        
        # Mark scan as completed
        self.update_progress("Scan completed", self.total_files)
        
        return self.get_summary()
    
    def get_summary(self) -> Dict:
        """Get summary of scan results."""
        total_size = sum(self.file_sizes.values())
        total_duplicate_size = sum(dup['duplicate_size'] for dup in self.duplicates)
        
        summary = {
            'categories': {},
            'duplicates': {
                'count': len(self.duplicates),
                'total_duplicate_size': total_duplicate_size,
                'total_duplicate_size_gb': round(total_duplicate_size / (1024**3), 2),
                'groups': self.duplicates
            },
            'total_size': total_size,
            'total_size_gb': round(total_size / (1024**3), 2)
        }
        
        for category, files in self.scan_results.items():
            size_gb = round(self.file_sizes[category] / (1024**3), 2)
            summary['categories'][category] = {
                'count': len(files),
                'total_size': self.file_sizes[category],
                'size_gb': size_gb,
                'percentage': round((self.file_sizes[category] / total_size * 100), 1) if total_size > 0 else 0,
                'files': files
            }
        
        return summary
    
    def delete_files(self, file_paths: List[str]) -> Dict:
        """Delete specified files and return results."""
        deleted = []
        failed = []
        total_size_freed = 0
        
        for filepath in file_paths:
            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted.append({
                    'path': filepath,
                    'size': file_size
                })
                total_size_freed += file_size
                print(f"Deleted: {filepath}")
            except Exception as e:
                failed.append({
                    'path': filepath,
                    'error': str(e)
                })
                print(f"Failed to delete {filepath}: {e}")
        
        return {
            'deleted': deleted,
            'failed': failed,
            'total_deleted': len(deleted),
            'total_failed': len(failed),
            'size_freed': total_size_freed,
            'size_freed_gb': round(total_size_freed / (1024**3), 2)
        }


if __name__ == "__main__":
    # Test the scanner
    scanner = SequencingFileScanner()
    
    # Create test data structure
    test_dir = "/workspace/test_data"
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(f"{test_dir}/raw", exist_ok=True)
    os.makedirs(f"{test_dir}/aligned", exist_ok=True)
    os.makedirs(f"{test_dir}/intermediate", exist_ok=True)
    
    # Create some test files
    test_files = [
        f"{test_dir}/raw/sample1_R1.fastq.gz",
        f"{test_dir}/raw/sample1_R2.fastq.gz",
        f"{test_dir}/aligned/sample1.sorted.bam",
        f"{test_dir}/aligned/sample1.sorted.bam.bai",
        f"{test_dir}/intermediate/sample1.metrics",
        f"{test_dir}/final_results.vcf.gz"
    ]
    
    for filepath in test_files:
        with open(filepath, 'w') as f:
            f.write(f"Test content for {os.path.basename(filepath)}\n" * 100)
    
    # Run scan
    results = scanner.scan_directory(test_dir)
    print(json.dumps(results, indent=2))
