import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/layout/sidebar';
import { TopNavbar } from '@/components/layout/top-navbar';
import { BackendStatusBanner } from '@/components/data-display/backend-status-banner';
import { DemoBanner } from '@/components/data-display/demo-banner';
import { WalkthroughModal } from '@/components/data-display/walkthrough-modal';

export const AppLayout: React.FC = () => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-finance-900">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <TopNavbar />

        {/* Demo Mode Identifier Banner */}
        <DemoBanner />

        {/* Live Backend Connectivity Indicator */}
        <BackendStatusBanner />

        {/* Page Viewport */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>

        {/* Floating Presenter Walkthrough Guide */}
        <WalkthroughModal />
      </div>
    </div>
  );
};
