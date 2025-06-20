import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'sonner';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { Scanner } from './components/Scanner';
import { FileCategories } from './components/FileCategories';
import { DuplicateFiles } from './components/DuplicateFiles';
import { Header } from './components/Header';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

export type ViewType = 'dashboard' | 'scanner' | 'categories' | 'duplicates';

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentView} />;
      case 'scanner':
        return <Scanner onNavigate={setCurrentView} />;
      case 'categories':
        return <FileCategories />;
      case 'duplicates':
        return <DuplicateFiles />;
      default:
        return <Dashboard onNavigate={setCurrentView} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
        <Sidebar currentView={currentView} onViewChange={setCurrentView} />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header currentView={currentView} />
          
          <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto">
              {renderCurrentView()}
            </div>
          </main>
        </div>
      </div>
      
      <Toaster 
        position="top-right" 
        richColors 
        theme="light"
        closeButton
      />
    </QueryClientProvider>
  );
}

export default App;
