import React from 'react';
import { ViewType } from '../App';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  BarChart3, 
  FolderSearch, 
  FileX, 
  Copy,
  Dna,
  Activity
} from 'lucide-react';
import { useQuery } from 'react-query';
import { sequencingAPI } from '../services/api';
import { isDemoMode } from '../services/mockData';
import { cn } from '../lib/utils';

interface SidebarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
}

const NAVIGATION_ITEMS = [
  {
    id: 'dashboard' as ViewType,
    label: 'Dashboard',
    icon: BarChart3,
    description: 'Overview & Analytics'
  },
  {
    id: 'scanner' as ViewType,
    label: 'Scanner',
    icon: FolderSearch,
    description: 'Scan Directories'
  },
  {
    id: 'categories' as ViewType,
    label: 'File Categories',
    icon: FileX,
    description: 'Browse by Type'
  },
  {
    id: 'duplicates' as ViewType,
    label: 'Duplicates',
    icon: Copy,
    description: 'Find Duplicates'
  }
];

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const { data: summary } = useQuery(
    'summary',
    sequencingAPI.getSummary,
    {
      refetchInterval: 10000,
      retry: 1,
      staleTime: 5000,
    }
  );

  const { data: scanStatus } = useQuery(
    'scanStatus',
    sequencingAPI.getScanStatus,
    {
      refetchInterval: 2000,
      retry: 1,
      staleTime: 1000,
    }
  );

  return (
    <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Logo/Brand */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Dna className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              SeqManager
            </h2>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Data Management
            </p>
          </div>
        </div>
      </div>

      {/* Status Panel */}
      {summary && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Data</span>
              <Badge variant="secondary" className="text-xs">
                {summary.total_size_gb.toFixed(1)} GB
              </Badge>
            </div>
            
            {summary.duplicates.count > 0 && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Duplicates</span>
                <Badge variant="destructive" className="text-xs">
                  {summary.duplicates.count}
                </Badge>
              </div>
            )}
            
            {scanStatus?.scanning && (
              <div className="flex items-center space-x-2">
                <Activity className="w-3 h-3 text-blue-600 animate-pulse" />
                <span className="text-sm text-blue-600 dark:text-blue-400">
                  Scanning... {scanStatus.progress}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {NAVIGATION_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            
            return (
              <li key={item.id}>
                <Button
                  variant={isActive ? "default" : "ghost"}
                  className={cn(
                    "w-full justify-start h-auto p-3",
                    isActive 
                      ? "bg-blue-600 text-white hover:bg-blue-700" 
                      : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  )}
                  onClick={() => onViewChange(item.id)}
                >
                  <Icon className={cn(
                    "w-5 h-5 mr-3",
                    isActive ? "text-white" : "text-gray-500 dark:text-gray-400"
                  )} />
                  <div className="text-left">
                    <div className="font-medium">{item.label}</div>
                    <div className={cn(
                      "text-xs",
                      isActive 
                        ? "text-blue-100" 
                        : "text-gray-500 dark:text-gray-400"
                    )}>
                      {item.description}
                    </div>
                  </div>
                </Button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Sequencing Data Manager v1.0
        </div>
      </div>
    </div>
  );
};
