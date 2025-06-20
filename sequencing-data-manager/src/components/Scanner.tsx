import React, { useState, useEffect } from 'react';
import { ViewType } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { 
  FolderSearch, 
  Play, 
  StopCircle, 
  CheckCircle,
  AlertCircle,
  Folder,
  Activity,
  BarChart3,
  Clock
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { sequencingAPI } from '../services/api';
import { toast } from 'sonner';

interface ScannerProps {
  onNavigate: (view: ViewType) => void;
}

export const Scanner: React.FC<ScannerProps> = ({ onNavigate }) => {
  const [directoryPath, setDirectoryPath] = useState('');
  const queryClient = useQueryClient();

  const { data: scanStatus, isLoading: statusLoading } = useQuery(
    'scanStatus',
    sequencingAPI.getScanStatus,
    {
      refetchInterval: 1000,
      refetchIntervalInBackground: true,
      retry: 1,
      staleTime: 500,
    }
  );

  const startScanMutation = useMutation(
    (path: string) => sequencingAPI.startScan(path),
    {
      onSuccess: (data) => {
        toast.success('Scan started successfully');
        // Invalidate and refetch scan status
        queryClient.invalidateQueries('scanStatus');
      },
      onError: (error: any) => {
        const message = error.response?.data?.error || 'Failed to start scan';
        toast.error(message);
      },
    }
  );

  const handleStartScan = () => {
    if (!directoryPath.trim()) {
      toast.error('Please enter a directory path');
      return;
    }
    startScanMutation.mutate(directoryPath.trim());
  };

  const handleViewResults = () => {
    queryClient.invalidateQueries('summary');
    queryClient.invalidateQueries('results');
    onNavigate('dashboard');
  };

  // Auto-refresh results when scan completes
  useEffect(() => {
    if (scanStatus && !scanStatus.scanning && scanStatus.progress === 100) {
      queryClient.invalidateQueries('summary');
      queryClient.invalidateQueries('results');
    }
  }, [scanStatus, queryClient]);

  const isScanning = scanStatus?.scanning || false;
  const hasError = scanStatus?.error;
  const isComplete = scanStatus?.progress === 100 && !isScanning;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FolderSearch className="w-6 h-6 mr-2 text-blue-600" />
            Directory Scanner
          </CardTitle>
          <CardDescription>
            Scan directories to analyze sequencing data files and identify optimization opportunities
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Scanner Input */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Scan Configuration</CardTitle>
          <CardDescription>
            Enter the path to the directory you want to analyze
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="directory-path">Directory Path</Label>
            <div className="flex space-x-2">
              <div className="flex-1 relative">
                <Folder className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="directory-path"
                  value={directoryPath}
                  onChange={(e) => setDirectoryPath(e.target.value)}
                  placeholder="/path/to/sequencing/data"
                  className="pl-10"
                  disabled={isScanning}
                />
              </div>
              <Button
                onClick={handleStartScan}
                disabled={isScanning || !directoryPath.trim() || startScanMutation.isLoading}
                size="default"
              >
                {isScanning ? (
                  <>
                    <StopCircle className="w-4 h-4 mr-2" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start Scan
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Example paths */}
          <div className="space-y-2">
            <Label className="text-sm text-gray-600">Example paths:</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {[
                '/data/sequencing',
                '/home/user/projects/genomics',
                '/mnt/storage/fastq',
                '/opt/bioinformatics/results'
              ].map((path) => (
                <Button
                  key={path}
                  variant="outline"
                  size="sm"
                  className="justify-start text-left"
                  onClick={() => setDirectoryPath(path)}
                  disabled={isScanning}
                >
                  <Folder className="w-3 h-3 mr-2" />
                  {path}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scan Status */}
      {(isScanning || isComplete || hasError) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              {isScanning && <Activity className="w-5 h-5 mr-2 text-blue-600 animate-pulse" />}
              {isComplete && <CheckCircle className="w-5 h-5 mr-2 text-green-600" />}
              {hasError && <AlertCircle className="w-5 h-5 mr-2 text-red-600" />}
              
              {isScanning && 'Scanning in Progress'}
              {isComplete && 'Scan Complete'}
              {hasError && 'Scan Error'}
            </CardTitle>
            <CardDescription>
              {isScanning && `Analyzing: ${scanStatus?.current_directory}`}
              {isComplete && 'Directory analysis completed successfully'}
              {hasError && 'An error occurred during scanning'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isScanning && (
              <>
                <div className="space-y-3">
                  <Progress value={scanStatus?.progress || 0} className="w-full h-3" />
                  
                  {/* Progress details */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Progress:</span>
                        <span className="font-medium">{scanStatus?.progress || 0}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Phase:</span>
                        <span className="font-medium text-blue-600">
                          {scanStatus?.phase || 'Initializing...'}
                        </span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Files Found:</span>
                        <span className="font-medium">{scanStatus?.total_files?.toLocaleString() || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Processed:</span>
                        <span className="font-medium text-green-600">
                          {scanStatus?.processed_files?.toLocaleString() || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Current status */}
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center text-gray-600">
                      <Activity className="w-3 h-3 mr-1 animate-pulse" />
                      {scanStatus?.phase || 'Working...'}
                    </span>
                    <span className="flex items-center text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      {scanStatus?.start_time ? 
                        `Started ${new Date(scanStatus.start_time).toLocaleTimeString()}` : 
                        'Processing...'
                      }
                    </span>
                  </div>
                </div>
              </>
            )}

            {isComplete && (
              <div className="space-y-4">
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    Scan completed successfully! You can now view the results and analyze your data.
                  </AlertDescription>
                </Alert>
                
                {/* Completion Summary */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Files:</span>
                      <span className="font-medium">{scanStatus?.total_files?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Directory:</span>
                      <span className="font-medium text-xs truncate max-w-32" title={scanStatus?.current_directory}>
                        {scanStatus?.current_directory?.split('/').pop() || 'N/A'}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Started:</span>
                      <span className="font-medium text-xs">
                        {scanStatus?.start_time ? 
                          new Date(scanStatus.start_time).toLocaleTimeString() : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Completed:</span>
                      <span className="font-medium text-xs">
                        {scanStatus?.end_time ? 
                          new Date(scanStatus.end_time).toLocaleTimeString() : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <Button onClick={handleViewResults} className="flex-1">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    View Dashboard
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => onNavigate('categories')}
                  >
                    Browse Files
                  </Button>
                </div>
              </div>
            )}

            {hasError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {scanStatus?.error}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Scan Instructions */}
      {!isScanning && !isComplete && !hasError && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">How to Use the Scanner</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                  1
                </div>
                <div>
                  <h4 className="font-medium">Enter Directory Path</h4>
                  <p className="text-sm text-gray-600">
                    Specify the full path to the directory containing your sequencing data files.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                  2
                </div>
                <div>
                  <h4 className="font-medium">Start the Scan</h4>
                  <p className="text-sm text-gray-600">
                    Click "Start Scan" to begin analyzing the directory structure and file types.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                  3
                </div>
                <div>
                  <h4 className="font-medium">Review Results</h4>
                  <p className="text-sm text-gray-600">
                    Once complete, explore the dashboard for insights, browse file categories, and identify duplicates.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scanner Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6 text-center">
            <FolderSearch className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <h3 className="font-semibold mb-1">Smart Detection</h3>
            <p className="text-sm text-gray-600">
              Automatically identifies sequencing file types and categories
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Activity className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <h3 className="font-semibold mb-1">Real-time Progress</h3>
            <p className="text-sm text-gray-600">
              Monitor scanning progress with live updates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <CheckCircle className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <h3 className="font-semibold mb-1">Comprehensive Analysis</h3>
            <p className="text-sm text-gray-600">
              Get detailed insights about storage usage and optimization
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
