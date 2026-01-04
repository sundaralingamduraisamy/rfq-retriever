import { Check, AlertTriangle, FileText, Upload } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Notification } from '@/data/mockData';
import { formatDistanceToNow } from 'date-fns';

interface ActivityFeedProps {
  notifications: Notification[];
  className?: string;
}

const iconMap = {
  success: Check,
  warning: AlertTriangle,
  info: FileText,
  error: AlertTriangle,
};

const colorMap = {
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  info: 'bg-primary/10 text-primary',
  error: 'bg-destructive/10 text-destructive',
};

export function ActivityFeed({ notifications, className }: ActivityFeedProps) {
  return (
    <div
      className={cn(
        'rounded-xl bg-card border border-border overflow-hidden',
        className
      )}
    >
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold">Recent Activity</h3>
      </div>

      <div className="divide-y divide-border">
        {notifications.map((notification, index) => {
          const Icon = iconMap[notification.type];
          
          return (
            <div
              key={notification.id}
              className={cn(
                'flex items-start gap-3 p-4',
                'animate-fade-in',
                !notification.read && 'bg-muted/30'
              )}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className={cn('p-2 rounded-lg', colorMap[notification.type])}>
                <Icon className="w-4 h-4" />
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{notification.title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {notification.message}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatDistanceToNow(new Date(notification.timestamp), {
                    addSuffix: true,
                  })}
                </p>
              </div>

              {!notification.read && (
                <div className="w-2 h-2 rounded-full bg-primary mt-2" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
