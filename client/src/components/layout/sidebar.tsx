import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  GitCompare,
  AlertOctagon,
  UserCheck,
  Receipt,
  BarChart3,
  FileText,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  tag?: string;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Reconciliation', path: '/reconciliation', icon: GitCompare },
  { label: 'Exceptions', path: '/exceptions', icon: AlertOctagon },
  { label: 'Review Queue', path: '/review', icon: UserCheck },
  { label: 'Transactions', path: '/transactions', icon: Receipt },
  { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  { label: 'Audit Trail', path: '/audit', icon: FileText },
  { label: 'Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-60 bg-finance-950 text-finance-300 flex flex-col shrink-0 border-r border-finance-800 select-none">
      {/* Brand Header */}
      <div className="h-14 flex items-center px-5 border-b border-finance-800/80 gap-3">
        <div className="w-7 h-7 rounded-md bg-brand-primary flex items-center justify-center text-white font-bold text-xs shadow-sm">
          RP
        </div>
        <div>
          <div className="text-xs font-bold text-white tracking-wider">RECONPILOT</div>
          <div className="text-[9px] text-brand-accent font-mono uppercase tracking-wider">AI Finance Controller</div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-2.5 py-3 space-y-1 overflow-y-auto">
        <div className="px-2.5 pb-2 text-[10px] font-semibold tracking-wider text-finance-500 uppercase">
          Operations
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2.5 px-2.5 py-2 rounded-md text-xs font-medium transition-all',
                  isActive
                    ? 'bg-finance-800/90 text-brand-accent font-semibold shadow-xs border-l-2 border-brand-primary'
                    : 'text-finance-400 hover:text-finance-100 hover:bg-finance-900/80'
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{item.label}</span>
              {item.tag && (
                <span className="ml-auto text-[9px] bg-finance-800 text-finance-400 px-1 py-0.5 rounded font-mono">
                  {item.tag}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Buildathon Track Badge */}
      <div className="p-3 border-t border-finance-800/80 bg-finance-900/40">
        <div className="flex items-center gap-1.5 text-xs text-finance-300 mb-0.5">
          <ShieldCheck className="w-3.5 h-3.5 text-brand-primary" />
          <span className="font-semibold text-white text-[11px]">Razorpay AI 2026</span>
        </div>
        <p className="text-[10px] text-finance-400 leading-tight">
          Track 4: AI Finance Controller
        </p>
        <div className="mt-1 text-[9px] text-brand-accent font-mono">
          Production Architecture
        </div>
      </div>
    </aside>
  );
};
