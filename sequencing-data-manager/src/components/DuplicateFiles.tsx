import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import { Alert, AlertDescription } from './ui/alert';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { 
  Copy, 
  Trash2, 
  ChevronDown, 
  ChevronRight,
  AlertTriangle,
  CheckSquare,
  Save,
  FolderOpen
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { sequencingAPI, formatFileSize, formatNumber } from '../services/api';
import { DuplicateGroup, FileItem } from '../types';
import { toast } from 'sonner';
import { DeleteConfirmationDialog } from './DeleteConfirmationDialog';

export const DuplicateFiles: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const queryClient = useQueryClient();

  const { data: duplicatesData, isLoading } = useQuery(
    'duplicates',
    sequencingAPI.getDuplicates,
    {
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
        queryClient.invalidateQueries('duplicates');
        queryClient.invalidateQueries('summary');
      },
      onError: (error: any) => {
        const message = error.response?.data?.error || 'Failed to delete files';
        toast.error(message);
      },
    }
  );

  const toggleGroup = (hash: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(hash)) {
      newExpanded.delete(hash);
    } else {
      newExpanded.add(hash);
    }
    setExpandedGroups(newExpanded);
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

  const handleSelectGroup = (group: DuplicateGroup, keepFirst: boolean = true) => {
    const filesToSelect = keepFirst ? group.files.slice(1) : group.files;
    const newSelected = new Set(selectedFiles);
    
    filesToSelect.forEach(file => {
      newSelected.add(file.path);
    });
    
    setSelectedFiles(newSelected);
  };

  const handleSelectAllDuplicates = () => {
    if (!duplicatesData?.groups) return;
    
    const newSelected = new Set<string>();
    duplicatesData.groups.forEach(group => {
      // Keep the first file of each group, select the rest
      group.files.slice(1).forEach(file => {
        newSelected.add(file.path);
      });
    });
    
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

  const selectedFilesList = useMemo(() => {
    if (!duplicatesData?.groups) return [];
    
    const allFiles: FileItem[] = [];
    duplicatesData.groups.forEach(group => {
      allFiles.push(...group.files);
    });
    
    return allFiles.filter(f => selectedFiles.has(f.path));
  }, [duplicatesData, selectedFiles]);

  const selectedTotalSize = selectedFilesList.reduce((acc, f) => acc + f.size_gb, 0);
  const potentialSavings = duplicatesData?.groups.reduce((acc, group) => {
    return acc + (group.files.slice(1).filter(f => selectedFiles.has(f.path)).length * group.files[0].size_gb);
  }, 0) || 0;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse"></div>
          </CardHeader>
        </Card>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-16 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!duplicatesData || duplicatesData.groups.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Copy className="w-6 h-6 mr-2 text-blue-600" />
              Duplicate Files
            </CardTitle>
            <CardDescription>
              No duplicate files found in the scanned directory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No Duplicates Found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-center">
                Great! Your directory doesn't contain any duplicate files.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Copy className="w-6 h-6 mr-2 text-blue-600" />
            Duplicate Files
          </CardTitle>
          <CardDescription>
            Identify and remove duplicate files to reclaim storage space
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {formatNumber(duplicatesData.groups.length)}
              </div>
              <div className="text-sm text-gray-600">Duplicate Groups</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {formatNumber(duplicatesData.count)}
              </div>
              <div className="text-sm text-gray-600">Total Duplicates</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {formatFileSize(duplicatesData.total_duplicate_size_gb)}
              </div>
              <div className="text-sm text-gray-600">Wasted Space</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {formatFileSize(potentialSavings)}
              </div>
              <div className="text-sm text-gray-600">Potential Savings</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <Button
              variant="outline"
              onClick={handleSelectAllDuplicates}
              disabled={duplicatesData.groups.length === 0}
            >
              <CheckSquare className="w-4 h-4 mr-2" />
              Select All Duplicates (Keep First)
            </Button>

            <Button
              variant="outline"
              onClick={() => setExpandedGroups(new Set(duplicatesData.groups.map(g => g.hash)))}
            >
              Expand All Groups
            </Button>

            <Button
              variant="outline"
              onClick={() => setExpandedGroups(new Set())}
            >
              Collapse All Groups
            </Button>

            {selectedFiles.size > 0 && (
              <Button
                variant="destructive"
                onClick={handleDeleteSelected}
                disabled={deleteFilesMutation.isLoading}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Selected ({formatNumber(selectedFiles.size)})
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Selection Summary */}
      {selectedFiles.size > 0 && (
        <Alert>
          <Save className="h-4 w-4" />
          <AlertDescription>
            {formatNumber(selectedFiles.size)} files selected • {formatFileSize(selectedTotalSize)} total size • 
            {formatFileSize(potentialSavings)} potential space savings
          </AlertDescription>
        </Alert>
      )}

      {/* Duplicate Groups */}
      <div className="space-y-4">
        {duplicatesData.groups.map((group, index) => (
          <Card key={group.hash}>
            <Collapsible
              open={expandedGroups.has(group.hash)}
              onOpenChange={() => toggleGroup(group.hash)}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {expandedGroups.has(group.hash) ? (
                        <ChevronDown className="w-5 h-5" />
                      ) : (
                        <ChevronRight className="w-5 h-5" />
                      )}
                      <div>
                        <CardTitle className="text-lg">
                          Duplicate Group #{index + 1}
                        </CardTitle>
                        <CardDescription>
                          {formatNumber(group.count)} identical files • {formatFileSize(group.size_gb)} each
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Badge variant="destructive">
                        {formatFileSize((group.count - 1) * group.size_gb)} wasted
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectGroup(group, true);
                        }}
                      >
                        Select Duplicates
                      </Button>
                    </div>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>

              <CollapsibleContent>
                <CardContent className="pt-0">
                  <div className="space-y-3">
                    {group.files.map((file, fileIndex) => (
                      <div
                        key={file.path}
                        className={`flex items-center space-x-3 p-3 border rounded-lg ${
                          fileIndex === 0 
                            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
                            : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                        }`}
                      >
                        <Checkbox
                          checked={selectedFiles.has(file.path)}
                          onCheckedChange={(checked) => handleSelectFile(file.path, checked as boolean)}
                          disabled={fileIndex === 0} // Suggest keeping the first file
                        />
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="font-medium truncate flex items-center">
                              {file.name}
                              {fileIndex === 0 && (
                                <Badge variant="secondary" className="ml-2">
                                  Keep (Original)
                                </Badge>
                              )}
                            </p>
                            <Badge variant="outline">{formatFileSize(file.size_gb)}</Badge>
                          </div>
                          <p className="text-sm text-gray-600 truncate">{file.path}</p>
                          <p className="text-xs text-gray-500">
                            Modified: {new Date(file.modified).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-medium text-yellow-800 dark:text-yellow-200">
                          Recommendation
                        </p>
                        <p className="text-yellow-700 dark:text-yellow-300">
                          Keep the first file (marked as "Original") and delete the duplicates to save {formatFileSize((group.count - 1) * group.size_gb)} of storage space.
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        ))}
      </div>

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
