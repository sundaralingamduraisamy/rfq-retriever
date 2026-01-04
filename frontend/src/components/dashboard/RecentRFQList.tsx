import { Link } from 'react-router-dom';
import { FileText, ChevronRight, Clock } from 'lucide-react';
import { RFQ } from '@/data/mockData';
import { StatusBadge } from '@/components/ui/status-badge';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface RecentRFQListProps {
  rfqs: RFQ[];
  className?: string;
}

export function RecentRFQList({ rfqs, className }: RecentRFQListProps) {
  return (
    <div
      className={cn(
        'rounded-xl bg-card border border-border overflow-hidden',
        className
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h3 className="font-semibold">Recently Generated RFQs</h3>
        <Link
          to="/rfqs"
          className="text-sm text-primary hover:underline flex items-center gap-1"
        >
          View all <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="divide-y divide-border">
        {rfqs.map((rfq, index) => (
          <Link
            key={rfq.id}
            to={`/rfqs/${rfq.id}`}
            className={cn(
              'flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors',
              'animate-fade-in'
            )}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="p-2.5 rounded-lg bg-primary/10">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="font-medium text-sm truncate">{rfq.title}</p>
                <StatusBadge status={rfq.status} />
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span className="font-mono">{rfq.reference}</span>
                <span>•</span>
                <span>{rfq.category}</span>
              </div>
            </div>

            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3.5 h-3.5" />
              <span>{formatDistanceToNow(new Date(rfq.updatedAt), { addSuffix: true })}</span>
            </div>

            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          </Link>
        ))}
      </div>
    </div>
  );
}
