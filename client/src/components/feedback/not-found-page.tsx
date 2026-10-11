import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FileQuestion, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-full bg-finance-100 flex items-center justify-center text-finance-500 mb-4">
        <FileQuestion className="w-8 h-8" />
      </div>
      <h1 className="text-2xl font-bold text-finance-900">Resource Not Found</h1>
      <p className="mt-2 text-sm text-finance-500 max-w-sm">
        The requested financial route or record identifier does not exist within the ReconPilot workspace.
      </p>
      <div className="mt-6">
        <Link to="/dashboard">
          <Button variant="outline" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Return to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};
