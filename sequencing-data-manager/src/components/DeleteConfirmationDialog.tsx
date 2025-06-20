import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { ScrollArea } from './ui/scroll-area';
import { 
  AlertTriangle, 
  Trash2, 
  File,
  X
} from 'lucide-react';
import { FileItem } from '../types';
import { formatFileSize, formatNumber } from '../services/api';

interface DeleteConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  files: FileItem[];
  onConfirm: () => void;
  isLoading: boolean;
}

export const DeleteConfirmationDialog: React.FC<DeleteConfirmationDialogProps> = ({
  open,
  onOpenChange,
  files,
  onConfirm,
  isLoading
}) => {
  const totalSize = files.reduce((acc, file) => acc + file.size_gb, 0);
  const fileCount = files.length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center text-red-600">
            <AlertTriangle className="w-5 h-5 mr-2" />
            Confirm File Deletion
          </DialogTitle>
          <DialogDescription>
            This action cannot be undone. The selected files will be permanently deleted from your system.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 space-y-4 overflow-hidden">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {formatNumber(fileCount)}
              </div>
              <div className="text-sm text-gray-600">Files to Delete</div>
            </div>
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {formatFileSize(totalSize)}
              </div>
              <div className="text-sm text-gray-600">Space to Free</div>
            </div>
          </div>

          {/* Warning */}
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Warning:</strong> Deleted files cannot be recovered unless you have a backup. 
              Please ensure these files are not needed before proceeding.
            </AlertDescription>
          </Alert>

          {/* File List */}
          <div className="border rounded-lg">
            <div className="p-3 bg-gray-50 dark:bg-gray-800 border-b">
              <h4 className="font-medium flex items-center">
                <File className="w-4 h-4 mr-2" />
                Files to be deleted:
              </h4>
            </div>
            <ScrollArea className="h-64">
              <div className="p-3 space-y-2">
                {files.map((file, index) => (
                  <div 
                    key={file.path}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{file.name}</p>
                      <p className="text-xs text-gray-600 truncate">{file.path}</p>
                    </div>
                    <Badge variant="outline" className="ml-2">
                      {formatFileSize(file.size_gb)}
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        <DialogFooter className="flex-shrink-0">
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button 
            variant="destructive" 
            onClick={onConfirm}
            disabled={isLoading}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            {isLoading ? 'Deleting...' : `Delete ${formatNumber(fileCount)} Files`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
