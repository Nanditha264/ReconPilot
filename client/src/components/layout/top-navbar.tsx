import React from 'react';
import { User, Bell, LogOut } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/hooks/use-auth';

export const TopNavbar: React.FC = () => {
  const { user, merchant, logout } = useAuth();

  return (
    <header className="h-14 bg-finance-900 border-b border-finance-700/80 px-4 md:px-6 flex items-center justify-between shrink-0 select-none">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-finance-400 hidden sm:inline">
          Organization:
        </span>
        <Badge variant="info" size="sm" className="font-mono text-xs truncate max-w-[200px]">
          {merchant?.name || 'ReconPilot Demo'}
        </Badge>
        <span className="text-[11px] text-finance-400 hidden lg:inline border-l border-finance-700 pl-3">
          Base: <span className="text-finance-200 font-mono font-medium">{merchant?.currency || 'INR'}</span> · Deterministic Engine + AI Reasoner
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button
          className="p-1.5 text-finance-400 hover:text-finance-100 rounded-md hover:bg-finance-800 transition-colors relative"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-brand-primary rounded-full"></span>
        </button>

        {/* User profile capsule */}
        <div className="flex items-center gap-2 pl-3 border-l border-finance-700/80">
          <div className="w-7 h-7 rounded-full bg-brand-primary/20 border border-brand-primary/40 text-brand-accent flex items-center justify-center font-bold text-xs">
            {user?.full_name?.charAt(0) || <User className="w-3.5 h-3.5" />}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-finance-100 flex items-center gap-1.5">
              <span className="truncate max-w-[140px]">{user?.full_name || 'Finance Controller'}</span>
              <Badge variant="neutral" size="sm" className="text-[9px] py-0 px-1 font-mono">
                {user?.role || 'ADMIN'}
              </Badge>
            </div>
            <div className="text-[10px] text-finance-400 font-mono truncate max-w-[160px]">
              {user?.email || 'admin@reconpilot.local'}
            </div>
          </div>

          {/* Logout button */}
          <button
            onClick={() => logout()}
            className="p-1.5 ml-1 text-finance-400 hover:text-rose-400 rounded-md hover:bg-finance-800 transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
