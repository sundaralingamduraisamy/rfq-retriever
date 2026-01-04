import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquarePlus,
  FileText,
  FolderOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Bell,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { currentUser, notifications } from '@/data/mockData';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: MessageSquarePlus, label: 'Generate RFQ', path: '/generate' },
  { icon: FileText, label: 'My RFQs', path: '/rfqs' },
  { icon: FolderOpen, label: 'Document Library', path: '/library' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const unreadNotifications = notifications.filter((n) => !n.read).length;

  return (
    <aside
      className={cn(
        'fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <Tooltip key={item.path} delayDuration={0}>
              <TooltipTrigger asChild>
                <NavLink
                  to={item.path}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                    'hover:bg-sidebar-accent',
                    isActive
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                      : 'text-sidebar-foreground'
                  )}
                >
                  <Icon
                    className={cn(
                      'w-5 h-5 flex-shrink-0',
                      isActive && 'text-primary'
                    )}
                  />
                  {!collapsed && (
                    <span className={cn('text-sm', isActive && 'font-medium')}>
                      {item.label}
                    </span>
                  )}
                </NavLink>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right" className="ml-2">
                  {item.label}
                </TooltipContent>
              )}
            </Tooltip>
          );
        })}
      </nav>

      {/* Notifications */}
      <div className="px-3 pb-2">
        <Tooltip delayDuration={0}>
          <TooltipTrigger asChild>
            <button
              className={cn(
                'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all duration-200',
                'hover:bg-sidebar-accent text-sidebar-foreground'
              )}
            >
              <div className="relative">
                <Bell className="w-5 h-5" />
                {unreadNotifications > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center text-[10px]"
                  >
                    {unreadNotifications}
                  </Badge>
                )}
              </div>
              {!collapsed && (
                <span className="text-sm">Notifications</span>
              )}
            </button>
          </TooltipTrigger>
          {collapsed && (
            <TooltipContent side="right" className="ml-2">
              Notifications
            </TooltipContent>
          )}
        </Tooltip>
      </div>

      {/* User Profile - Removed and moved to Header */}

      {/* Collapse Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className={cn(
          'absolute top-1/2 -translate-y-1/2 -right-3 w-6 h-6',
          'bg-card border border-border rounded-full',
          'flex items-center justify-center',
          'hover:bg-secondary transition-colors',
          'shadow-sm'
        )}
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4" />
        ) : (
          <ChevronLeft className="w-4 h-4" />
        )}
      </button>
    </aside>
  );
}
