import React from 'react';
import { ViewType } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  HardDrive, 
  Files, 
  Copy, 
  AlertTriangle,
  TrendingUp,
  FolderSearch,
  BarChart3
} from 'lucide-react';
import { useQuery } from 'react-query';
import { sequencingAPI, formatFileSize, formatNumber } from '../services/api';
import { CATEGORY_LABELS, CATEGORY_COLORS } from '../types';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { isDemoMode } from '../services/mockData';

interface DashboardProps {
  onNavigate: (view: ViewType) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const { data: summary, isLoading, error } = useQuery(
    'summary',
    sequencingAPI.getSummary,
    {
      refetchInterval: isDemoMode() ? false : 10000,
      retry: 1,
      staleTime: 5000,
    }
  );

  const { data: scanStatus } = useQuery(
    'scanStatus',
    sequencingAPI.getScanStatus,
    {
      refetchInterval: isDemoMode() ? false : 2000,
      retry: 1,
      staleTime: 1000,
    }
  );

  // Prepare chart data
  const categoryChartData = summary ? Object.entries(summary.categories).map(([key, data]) => ({
    name: CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS] || key,
    value: data.size_gb,
    count: data.count,
    color: CATEGORY_COLORS[key as keyof typeof CATEGORY_COLORS] || '#6B7280'
  })) : [];

  const sizeDistributionData = summary ? Object.entries(summary.categories).map(([key, data]) => ({
    category: CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS] || key,
    size: data.size_gb,
    files: data.count
  })) : [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <FolderSearch className="w-16 h-16 text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          No Data Available
        </h3>
        <p className="text-gray-600 dark:text-gray-400 text-center mb-6 max-w-md">
          Start by scanning a directory to analyze your sequencing data files and get comprehensive insights.
        </p>
        <Button onClick={() => onNavigate('scanner')} size="lg">
          <FolderSearch className="w-5 h-5 mr-2" />
          Start Scanning
        </Button>
      </div>
    );
  }

  const totalFiles = Object.values(summary.categories).reduce((acc, cat) => acc + cat.count, 0);

  return (
    <div className="space-y-6">
      {/* Demo Mode Banner */}
      {isDemoMode() && (
        <Card className="border-purple-200 bg-purple-50 dark:bg-purple-900/20 dark:border-purple-800">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-purple-600 rounded-lg">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-purple-900 dark:text-purple-100">
                  Demo Mode Active
                </h3>
                <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
                  You're viewing sample sequencing data. This demonstrates how SeqManager would analyze your actual genomics files. 
                  To analyze real data, deploy with the Flask backend and point it to your sequencing directories.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Storage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatFileSize(summary.total_size_gb)}</div>
            <p className="text-xs text-muted-foreground">
              Across all categories
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Files</CardTitle>
            <Files className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalFiles)}</div>
            <p className="text-xs text-muted-foreground">
              Files analyzed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Duplicates</CardTitle>
            <Copy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(summary.duplicates.count)}</div>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(summary.duplicates.size_gb)} reclaimable
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(summary.categories).length}</div>
            <p className="text-xs text-muted-foreground">
              File categories found
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Scanning Status */}
      {scanStatus?.scanning && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
              Scanning in Progress
            </CardTitle>
            <CardDescription>
              Currently scanning: {scanStatus.current_directory}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Progress value={scanStatus.progress} className="w-full" />
            <p className="text-sm text-gray-600 mt-2">
              {scanStatus.progress}% complete
            </p>
          </CardContent>
        </Card>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Storage Distribution Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Storage Distribution</CardTitle>
            <CardDescription>
              Data usage by file category
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [formatFileSize(value), 'Size']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* File Count by Category */}
        <Card>
          <CardHeader>
            <CardTitle>Files by Category</CardTitle>
            <CardDescription>
              Number of files in each category
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sizeDistributionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="category" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                  />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="files" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Category Details</CardTitle>
          <CardDescription>
            Detailed breakdown of file categories
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(summary.categories).map(([key, data]) => (
              <div key={key} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-4 h-4 rounded" 
                    style={{ backgroundColor: CATEGORY_COLORS[key as keyof typeof CATEGORY_COLORS] }}
                  />
                  <div>
                    <h4 className="font-medium">
                      {CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS] || key}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {formatNumber(data.count)} files • {formatFileSize(data.size_gb)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary">
                    {data.percentage.toFixed(1)}%
                  </Badge>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => onNavigate('categories')}
                  >
                    View Files
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => onNavigate('scanner')}>
          <CardContent className="p-6 text-center">
            <FolderSearch className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <h3 className="font-semibold mb-1">Start New Scan</h3>
            <p className="text-sm text-gray-600">Analyze another directory</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => onNavigate('categories')}>
          <CardContent className="p-6 text-center">
            <Files className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <h3 className="font-semibold mb-1">Browse Files</h3>
            <p className="text-sm text-gray-600">Explore by category</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => onNavigate('duplicates')}>
          <CardContent className="p-6 text-center">
            <Copy className="w-8 h-8 text-orange-600 mx-auto mb-2" />
            <h3 className="font-semibold mb-1">Find Duplicates</h3>
            <p className="text-sm text-gray-600">Reclaim storage space</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
