import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Database,
  Zap,
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { RecentRFQList } from '@/components/dashboard/RecentRFQList';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { ActivityFeed } from '@/components/dashboard/ActivityFeed';
import { currentUser, recentRFQs, notifications, dashboardStats } from '@/data/mockData';

export default function Dashboard() {
  const user = JSON.parse(localStorage.getItem("user") || '{"name": "Guest", "role": "Visitor"}');

  return (
    <MainLayout>
      <div className="p-6 lg:p-8 space-y-8">
        {/* Header */}
        <div className="animate-fade-in">
          <h1 className="text-2xl font-bold">
            Welcome back, <span className="gradient-text">{user.name.split(' ')[0]}</span>
          </h1>
          <p className="text-muted-foreground mt-1">
            Here's an overview of your RFQ generation activity
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Total RFQs Generated"
            value={dashboardStats.totalRFQs}
            subtitle="All time"
            icon={FileText}
            trend={{ value: 12, positive: true }}
          />
          <StatsCard
            title="This Month"
            value={dashboardStats.thisMonth}
            subtitle="December 2025"
            icon={Zap}
          />
          <StatsCard
            title="Pending Review"
            value={dashboardStats.pendingReview}
            subtitle="Awaiting approval"
            icon={AlertCircle}
          />
          <StatsCard
            title="Approved"
            value={dashboardStats.approved}
            subtitle="Ready to send"
            icon={CheckCircle}
          />
        </div>

        {/* Knowledge Base Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatsCard
            title="Knowledge Base Documents"
            value={dashboardStats.knowledgeBaseDocuments.toLocaleString()}
            subtitle="Historical RFQs & templates"
            icon={Database}
          />
          <StatsCard
            title="Average Generation Time"
            value={dashboardStats.averageGenerationTime}
            subtitle="AI-powered drafting"
            icon={Clock}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent RFQs - Takes 2 columns */}
          <div className="lg:col-span-2">
            <RecentRFQList rfqs={recentRFQs.slice(0, 5)} />
          </div>

          {/* Sidebar - Quick Actions & Activity */}
          <div className="space-y-6">
            <QuickActions />
            <ActivityFeed notifications={notifications} />
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
