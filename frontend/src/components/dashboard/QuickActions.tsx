import { Link } from 'react-router-dom';
import { Plus, Upload, Search, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

const actions = [
  {
    icon: Plus,
    label: 'Generate New RFQ',
    description: 'Create with AI assistance',
    path: '/generate',
    primary: true,
  },
  {
    icon: Upload,
    label: 'Upload Document',
    description: 'Add to knowledge base',
    path: '/library',
  },
  {
    icon: Search,
    label: 'Search RFQs',
    description: 'Find historical documents',
    path: '/rfqs',
  },
];

export function QuickActions() {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
        Quick Actions
      </h3>
      <div className="space-y-2">
        {actions.map((action) => (
          <Link
            key={action.path}
            to={action.path}
            className={cn(
              'flex items-center gap-3 p-4 rounded-xl border transition-all duration-200',
              action.primary
                ? 'bg-gradient-to-r from-primary/10 to-accent/10 border-primary/30 hover:border-primary/50 glow'
                : 'bg-card border-border hover:border-primary/30'
            )}
          >
            <div
              className={cn(
                'p-2.5 rounded-lg',
                action.primary ? 'bg-primary/20' : 'bg-muted'
              )}
            >
              <action.icon
                className={cn(
                  'w-5 h-5',
                  action.primary ? 'text-primary' : 'text-muted-foreground'
                )}
              />
            </div>
            <div>
              <p
                className={cn(
                  'font-medium text-sm',
                  action.primary && 'text-primary'
                )}
              >
                {action.label}
              </p>
              <p className="text-xs text-muted-foreground">
                {action.description}
              </p>
            </div>
            {action.primary && (
              <Sparkles className="w-4 h-4 text-primary ml-auto animate-pulse" />
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
