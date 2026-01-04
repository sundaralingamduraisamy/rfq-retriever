import { cn } from '@/lib/utils';

type Status = 'draft' | 'in_review' | 'approved' | 'sent';

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

const statusConfig: Record<Status, { label: string; className: string }> = {
  draft: {
    label: 'Draft',
    className: 'bg-muted text-muted-foreground',
  },
  in_review: {
    label: 'In Review',
    className: 'bg-warning/10 text-warning border border-warning/20',
  },
  approved: {
    label: 'Approved',
    className: 'bg-success/10 text-success border border-success/20',
  },
  sent: {
    label: 'Sent',
    className: 'bg-primary/10 text-primary border border-primary/20',
  },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}
