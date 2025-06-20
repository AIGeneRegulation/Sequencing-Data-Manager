// Mock data for demo when backend is not available
import { ScanStatus, ScanResults, Summary, CategoryData, DuplicatesData, FileItem } from '../types';

// Mock file items
const mockFiles: FileItem[] = [
  {
    path: '/data/sequencing/sample1_R1.fastq.gz',
    name: 'sample1_R1.fastq.gz',
    size: 2147483648, // 2GB in bytes
    size_gb: 2.0,
    modified: '2024-06-15T10:30:00Z',
    extension: '.fastq.gz'
  },
  {
    path: '/data/sequencing/sample1_R2.fastq.gz',
    name: 'sample1_R2.fastq.gz',
    size: 2147483648,
    size_gb: 2.0,
    modified: '2024-06-15T10:30:00Z',
    extension: '.fastq.gz'
  },
  {
    path: '/data/aligned/sample1.sorted.bam',
    name: 'sample1.sorted.bam',
    size: 1073741824, // 1GB
    size_gb: 1.0,
    modified: '2024-06-15T12:00:00Z',
    extension: '.bam'
  },
  {
    path: '/data/aligned/sample1.bai',
    name: 'sample1.bai',
    size: 104857600, // 100MB
    size_gb: 0.1,
    modified: '2024-06-15T12:05:00Z',
    extension: '.bai'
  },
  {
    path: '/data/variants/sample1.vcf.gz',
    name: 'sample1.vcf.gz',
    size: 52428800, // 50MB
    size_gb: 0.05,
    modified: '2024-06-15T14:00:00Z',
    extension: '.vcf.gz'
  },
  {
    path: '/data/temp/temp_file1.tmp',
    name: 'temp_file1.tmp',
    size: 536870912, // 500MB
    size_gb: 0.5,
    modified: '2024-06-14T09:00:00Z',
    extension: '.tmp'
  }
];

export const mockScanStatus: ScanStatus = {
  scanning: false,
  progress: 100,
  current_directory: '/data/sequencing',
  error: null,
  phase: 'Completed',
  total_files: 156,
  processed_files: 156,
  start_time: '2024-06-19T14:30:00Z',
  end_time: '2024-06-19T14:32:15Z'
};

export const mockSummary: Summary = {
  total_size_gb: 5.65,
  categories: {
    raw_sequencing: {
      count: 2,
      size_gb: 4.0,
      percentage: 70.8
    },
    aligned_data: {
      count: 2,
      size_gb: 1.1,
      percentage: 19.5
    },
    intermediate_files: {
      count: 1,
      size_gb: 0.05,
      percentage: 0.9
    },
    final_outputs: {
      count: 0,
      size_gb: 0.0,
      percentage: 0.0
    },
    other: {
      count: 1,
      size_gb: 0.5,
      percentage: 8.8
    }
  },
  duplicates: {
    count: 2,
    size_gb: 1.0
  }
};

export const mockCategoryData: Record<string, CategoryData> = {
  raw_sequencing: {
    count: 2,
    size_gb: 4.0,
    percentage: 70.8,
    files: mockFiles.filter(f => f.extension === '.fastq.gz')
  },
  aligned_data: {
    count: 2,
    size_gb: 1.1,
    percentage: 19.5,
    files: mockFiles.filter(f => f.extension === '.bam' || f.extension === '.bai')
  },
  intermediate_files: {
    count: 1,
    size_gb: 0.05,
    percentage: 0.9,
    files: mockFiles.filter(f => f.extension === '.vcf.gz')
  },
  final_outputs: {
    count: 0,
    size_gb: 0.0,
    percentage: 0.0,
    files: []
  },
  other: {
    count: 1,
    size_gb: 0.5,
    percentage: 8.8,
    files: mockFiles.filter(f => f.extension === '.tmp')
  }
};

export const mockDuplicatesData: DuplicatesData = {
  count: 2,
  total_duplicate_size_gb: 1.0,
  groups: [
    {
      hash: 'abc123def456',
      count: 2,
      size_gb: 0.5,
      files: [
        {
          path: '/data/temp/temp_file1.tmp',
          name: 'temp_file1.tmp',
          size: 536870912,
          size_gb: 0.5,
          modified: '2024-06-14T09:00:00Z',
          extension: '.tmp'
        },
        {
          path: '/data/backup/temp_file1_copy.tmp',
          name: 'temp_file1_copy.tmp',
          size: 536870912,
          size_gb: 0.5,
          modified: '2024-06-14T09:00:00Z',
          extension: '.tmp'
        }
      ]
    }
  ]
};

export const mockScanResults: ScanResults = {
  total_size_gb: 5.65,
  scan_time: '2024-06-19T13:30:00Z',
  directory_path: '/data/sequencing',
  categories: mockCategoryData,
  duplicates: mockDuplicatesData
};

// Check if we're in demo mode (no backend available)
export const isDemoMode = () => {
  return window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
};
