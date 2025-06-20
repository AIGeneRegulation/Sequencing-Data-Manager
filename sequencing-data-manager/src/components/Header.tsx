import React from 'react';
import { ViewType } from '../App';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { RefreshCw, Settings, Eye } from 'lucide-react';
import { useQuery } from 'react-query';
import { sequencingAPI } from '../services/api';
import { isDemoMode } from '../services/mockData';

interface HeaderProps {
  currentView: ViewType;
}

const VIEW_TITLES: Record<ViewType, string> = {
  dashboard: 'Dashboard',
  scanner: 'Directory Scanner',
  categories: 'File Categories',
  duplicates: 'Duplicate Files'
};

const VIEW_DESCRIPTIONS: Record<ViewType, string> = {
  dashboard: 'Overview of your sequencing data analysis',
  scanner: 'Scan directories for sequencing files',
  categories: 'Browse files organized by type',
  duplicates: 'Identify and manage duplicate files'
};

export const Header: React.FC<HeaderProps> = ({ currentView }) => {
  const { data: scanStatus } = useQuery(
    'scanStatus',
    sequencingAPI.getScanStatus,
    {
      refetchInterval: 2000,
      enabled: true,
      retry: 1,
      staleTime: 1000,
    }
  );

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {VIEW_TITLES[currentView]}
              </h1>
              {isDemoMode() && (
                <Badge variant="secondary" className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                  <Eye className="w-3 h-3 mr-1" />
                  Demo Mode
                </Badge>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {VIEW_DESCRIPTIONS[currentView]}
              {isDemoMode() && ' • Showing sample data'}
            </p>
          </div>
          
          {scanStatus?.scanning && (
            <Badge variant="default" className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
              Scanning...
            </Badge>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            className="hidden sm:flex"
          >
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>
    </header>
  );
};
