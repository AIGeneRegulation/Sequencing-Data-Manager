import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Files, 
  Search, 
  SortAsc, 
  SortDesc, 
  Filter,
  Trash2,
  CheckSquare,
  Square,
  Download,
  AlertTriangle,
  FolderOpen
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { sequencingAPI, formatFileSize, formatNumber } from '../services/api';
import { CATEGORY_LABELS, CATEGORY_COLORS, FileItem, CategoryData } from '../types';
import { toast } from 'sonner';
import { DeleteConfirmationDialog } from './DeleteConfirmationDialog';

type SortField = 'name' | 'size' | 'modified';
type SortOrder = 'asc' | 'desc';

export const FileCategories: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('size');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [sizeFilter, setSizeFilter] = useState<string>('all');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>('');

  const queryClient = useQueryClient();

  const { data: summary } = useQuery(
    'summary',
    sequencingAPI.getSummary,
    {
      retry: 1,
      staleTime: 5000,
    }
  );

  const { data: categoryData, isLoading: categoryLoading } = useQuery(
    ['category', activeCategory],
    () => sequencingAPI.getFilesByCategory(activeCategory),
    {
      enabled: !!activeCategory,
      retry: 1,
      staleTime: 5000,
    }
  );

  const deleteFilesMutation = useMutation(
    (filePaths: string[]) => sequencingAPI.deleteFiles(filePaths),
    {
      onSuccess: (result) => {
        toast.success(`Deleted ${result.total_deleted} files, freed ${formatFileSize(result.space_freed_gb)}`);
        setSelectedFiles(new Set());
        setShowDeleteDialog(false);
        queryClient.invalidateQueries('summary');
        queryClient.invalidateQueries(['category', activeCategory]);
      },
      onError: (error: any) => {
        const message = error.response?.data?.error || 'Failed to delete files';
        toast.error(message);
      },
    }
  );

  // Filter and sort files
  const filteredFiles = useMemo(() => {
    if (!categoryData?.files) return [];

    let filtered = categoryData.files.filter(file => {
      // Search filter
      if (searchTerm && !file.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Size filter
      if (sizeFilter !== 'all') {
        const sizeGB = file.size_gb;
        switch (sizeFilter) {
          case 'small':
            if (sizeGB >= 0.1) return false;
            break;
          case 'medium':
            if (sizeGB < 0.1 || sizeGB >= 1) return false;
            break;
          case 'large':
            if (sizeGB < 1) return false;
            break;
        }
      }

      return true;
    });

    // Sort files
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortField) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'size':
          aValue = a.size;
          bValue = b.size;
          break;
        case 'modified':
          aValue = new Date(a.modified);
          bValue = new Date(b.modified);
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [categoryData?.files, searchTerm, sortField, sortOrder, sizeFilter]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedFiles(new Set(filteredFiles.map(f => f.path)));
    } else {
      setSelectedFiles(new Set());
    }
  };

  const handleSelectFile = (filePath: string, checked: boolean) => {
    const newSelected = new Set(selectedFiles);
    if (checked) {
      newSelected.add(filePath);
    } else {
      newSelected.delete(filePath);
    }
    setSelectedFiles(newSelected);
  };

  const handleDeleteSelected = () => {
    if (selectedFiles.size > 0) {
      setShowDeleteDialog(true);
    }
  };

  const confirmDelete = () => {
    deleteFilesMutation.mutate(Array.from(selectedFiles));
  };

  const selectedFilesList = filteredFiles.filter(f => selectedFiles.has(f.path));
  const selectedTotalSize = selectedFilesList.reduce((acc, f) => acc + f.size_gb, 0);

  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <FolderOpen className="w-16 h-16 text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          No Data Available
        </h3>
        <p className="text-gray-600 dark:text-gray-400 text-center">
          Please scan a directory first to view file categories.
        </p>
      </div>
    );
  }

  const categories = Object.keys(summary.categories);

  // Set initial active category
  if (!activeCategory && categories.length > 0) {
    setActiveCategory(categories[0]);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Files className="w-6 h-6 mr-2 text-blue-600" />
            File Categories
          </CardTitle>
          <CardDescription>
            Browse and manage files organized by type and category
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Category Tabs */}
      <Tabs value={activeCategory} onValueChange={setActiveCategory}>
        <TabsList className="grid w-full grid-cols-3 lg:grid-cols-5">
          {categories.map((category) => {
            const data = summary.categories[category];
            return (
              <TabsTrigger key={category} value={category} className="relative">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded" 
                    style={{ backgroundColor: CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] }}
                  />
                  <span className="truncate">
                    {CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS] || category}
                  </span>
                  <Badge variant="secondary" className="text-xs">
                    {data.count}
                  </Badge>
                </div>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {categories.map((category) => (
          <TabsContent key={category} value={category} className="space-y-4">
            {/* Category Stats */}
            <Card>
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {formatNumber(summary.categories[category].count)}
                    </div>
                    <div className="text-sm text-gray-600">Files</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {formatFileSize(summary.categories[category].size_gb)}
                    </div>
                    <div className="text-sm text-gray-600">Total Size</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {summary.categories[category].percentage.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">of Total</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {formatNumber(selectedFiles.size)}
                    </div>
                    <div className="text-sm text-gray-600">Selected</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Controls */}
            <Card>
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex-1 min-w-64">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Search files..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <Select value={sortField} onValueChange={(value: SortField) => setSortField(value)}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="name">Name</SelectItem>
                      <SelectItem value="size">Size</SelectItem>
                      <SelectItem value="modified">Modified</SelectItem>
                    </SelectContent>
                  </Select>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  >
                    {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
                  </Button>

                  <Select value={sizeFilter} onValueChange={setSizeFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Sizes</SelectItem>
                      <SelectItem value="small">&lt; 100 MB</SelectItem>
                      <SelectItem value="medium">100 MB - 1 GB</SelectItem>
                      <SelectItem value="large">&gt; 1 GB</SelectItem>
                    </SelectContent>
                  </Select>

                  {selectedFiles.size > 0 && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleDeleteSelected}
                      disabled={deleteFilesMutation.isLoading}
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Selected
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Selection Summary */}
            {selectedFiles.size > 0 && (
              <Alert>
                <CheckSquare className="h-4 w-4" />
                <AlertDescription>
                  {formatNumber(selectedFiles.size)} files selected • {formatFileSize(selectedTotalSize)} total size
                </AlertDescription>
              </Alert>
            )}

            {/* File List */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">
                    {CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS] || category} Files
                  </CardTitle>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="select-all"
                      checked={selectedFiles.size === filteredFiles.length && filteredFiles.length > 0}
                      onCheckedChange={handleSelectAll}
                    />
                    <label htmlFor="select-all" className="text-sm font-medium">
                      Select All ({formatNumber(filteredFiles.length)})
                    </label>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {categoryLoading ? (
                  <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="h-16 bg-gray-200 rounded animate-pulse" />
                    ))}
                  </div>
                ) : filteredFiles.length === 0 ? (
                  <div className="text-center py-8">
                    <Files className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No files found matching current filters</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filteredFiles.slice(0, 100).map((file) => (
                      <div
                        key={file.path}
                        className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                      >
                        <Checkbox
                          checked={selectedFiles.has(file.path)}
                          onCheckedChange={(checked) => handleSelectFile(file.path, checked as boolean)}
                        />
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="font-medium truncate">{file.name}</p>
                            <Badge variant="outline">{formatFileSize(file.size_gb)}</Badge>
                          </div>
                          <p className="text-sm text-gray-600 truncate">{file.path}</p>
                          <p className="text-xs text-gray-500">
                            Modified: {new Date(file.modified).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    
                    {filteredFiles.length > 100 && (
                      <div className="text-center py-4">
                        <p className="text-gray-600">
                          Showing first 100 of {formatNumber(filteredFiles.length)} files
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmationDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        files={selectedFilesList}
        onConfirm={confirmDelete}
        isLoading={deleteFilesMutation.isLoading}
      />
    </div>
  );
};
