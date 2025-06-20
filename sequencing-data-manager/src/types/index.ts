// Types for the Sequencing Data Management System

export interface ScanStatus {
  scanning: boolean;
  progress: number;
  current_directory: string;
  error: string | null;
  phase: string;
  total_files: number;
  processed_files: number;
  start_time: string | null;
  end_time: string | null;
}

export interface FileItem {
  path: string;
  name: string;
  size: number;
  size_gb: number;
  modified: string;
  extension: string;
}

export interface CategoryData {
  count: number;
  size_gb: number;
  percentage: number;
  files: FileItem[];
}

export interface DuplicateGroup {
  hash: string;
  files: FileItem[];
  size_gb: number;
  count: number;
}

export interface DuplicatesData {
  count: number;
  total_duplicate_size_gb: number;
  groups: DuplicateGroup[];
}

export interface ScanResults {
  total_size_gb: number;
  scan_time: string;
  directory_path: string;
  categories: {
    [key: string]: CategoryData;
  };
  duplicates: DuplicatesData;
}

export interface Summary {
  total_size_gb: number;
  categories: {
    [key: string]: {
      count: number;
      size_gb: number;
      percentage: number;
    };
  };
  duplicates: {
    count: number;
    size_gb: number;
  };
}

export interface DeleteResult {
  total_deleted: number;
  total_failed: number;
  deleted_files: string[];
  failed_files: string[];
  space_freed_gb: number;
}

export type CategoryType = 'raw_sequencing' | 'aligned_data' | 'intermediate_files' | 'final_outputs' | 'other';

export const CATEGORY_LABELS: Record<CategoryType, string> = {
  raw_sequencing: 'Raw Sequencing Data',
  aligned_data: 'Aligned Data',
  intermediate_files: 'Intermediate Files',
  final_outputs: 'Final Outputs',
  other: 'Other Files'
};

export const CATEGORY_COLORS: Record<CategoryType, string> = {
  raw_sequencing: '#3B82F6', // Blue
  aligned_data: '#10B981', // Green
  intermediate_files: '#F59E0B', // Yellow
  final_outputs: '#EF4444', // Red
  other: '#6B7280' // Gray
};
