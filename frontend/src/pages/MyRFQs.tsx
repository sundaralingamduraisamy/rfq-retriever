import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Search,
  Plus,
  MoreVertical,
  Trash2,
  Edit2,
  Download,
  Filter,
  Eye
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { formatDistanceToNow, format } from 'date-fns';
import { cn } from '@/lib/utils';
import { DocumentPreviewDialog } from '@/components/common/DocumentPreviewDialog';
import { getRfqs, deleteRfq, updateRfqStatus, getRfqDetail } from '@/api';

type RFQItem = {
  id: number;
  title: string;
  status: string;
  updated_at: string;
  created_at: string;
};

const statusStyles: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-100",
  review: "bg-blue-100 text-blue-700 border-blue-200 hover:bg-blue-100",
  approved: "bg-green-100 text-green-700 border-green-200 hover:bg-green-100",
  rejected: "bg-red-100 text-red-700 border-red-200 hover:bg-red-100",
};

export default function MyRFQs() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [rfqs, setRfqs] = useState<RFQItem[]>([]);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [rfqToDelete, setRfqToDelete] = useState<number | null>(null);

  // Preview State
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState<{ id: number, title: string, content: string } | null>(null);

  const fetchRfqs = () => {
    getRfqs().then((data) => {
      setRfqs(data.rfqs || []);
    }).catch(console.error);
  };

  useEffect(() => {
    fetchRfqs();
  }, []);

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await updateRfqStatus(id, newStatus);
      // Optimistic update
      setRfqs(prev => prev.map(item =>
        item.id === id ? { ...item, status: newStatus } : item
      ));
    } catch (e) {
      alert("Failed to update status");
    }
  };

  const filteredRFQs = rfqs.filter((item) => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDelete = (id: number) => {
    setRfqToDelete(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!rfqToDelete) return;
    try {
      await deleteRfq(rfqToDelete);
      fetchRfqs();
    } catch (error) {
      alert("Delete failed");
    } finally {
      setDeleteDialogOpen(false);
      setRfqToDelete(null);
    }
  };

  const handleEdit = (id: number) => {
    navigate("/generate", { state: { rfqId: id } });
  };

  const handleView = async (id: number) => {
    try {
      const detailed = await getRfqDetail(id);
      setPreviewContent(detailed);
      setPreviewOpen(true);
    } catch (e) {
      alert("Failed to load RFQ details");
    }
  };

  return (
    <MainLayout>
      <div className="p-6 lg:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">My RFQs</h1>
            <p className="text-muted-foreground mt-1">
              Manage, track, and edit your generated RFQs.
            </p>
          </div>
          <Link to="/generate">
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Generate New RFQ
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search RFQs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
              <Filter className="w-4 h-4 mr-2 text-muted-foreground" />
              <SelectValue placeholder="Filter by Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="review">In Review</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-soft-sm overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-50/50 border-b border-slate-100">
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[40%] pl-6 py-4 text-xs font-semibold uppercase tracking-wider text-slate-500">RFQ Title</TableHead>
                <TableHead className="w-[20%] text-xs font-semibold uppercase tracking-wider text-slate-500">Status</TableHead>
                <TableHead className="w-[20%] text-xs font-semibold uppercase tracking-wider text-slate-500">Created At</TableHead>
                <TableHead className="w-[20%] text-right pr-6 text-xs font-semibold uppercase tracking-wider text-slate-500">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRFQs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-32 text-center text-muted-foreground">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center">
                        <Filter className="w-5 h-5 text-slate-400" />
                      </div>
                      <p>No RFQs found matching your criteria</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredRFQs.map((item) => (
                  <TableRow key={item.id} className="group hover:bg-slate-50/80 transition-colors border-b border-slate-50 last:border-0">
                    <TableCell className="font-medium pl-6 py-4">
                      <div className="flex flex-col gap-1">
                        <span className="text-slate-700 font-semibold group-hover:text-primary transition-colors">{item.title}</span>
                        <span className="text-[11px] text-slate-400 font-mono">ID: #{item.id}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-auto p-0 hover:bg-transparent">
                            <Badge
                              variant="outline"
                              className={cn(
                                "cursor-pointer px-2.5 py-0.5 rounded-full text-xs font-medium border shadow-none transition-all",
                                statusStyles[item.status] || statusStyles.draft
                              )}
                            >
                              {item.status === 'review' ? 'In Review' : item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                            </Badge>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start" className="w-32">
                          <DropdownMenuItem onClick={() => handleStatusChange(item.id, 'draft')}>
                            <div className="w-2 h-2 rounded-full bg-gray-400 mr-2" /> Draft
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleStatusChange(item.id, 'review')}>
                            <div className="w-2 h-2 rounded-full bg-blue-500 mr-2" /> In Review
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleStatusChange(item.id, 'approved')}>
                            <div className="w-2 h-2 rounded-full bg-green-500 mr-2" /> Approved
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {item.created_at ? format(new Date(item.created_at), "MMM d, yyyy") : '-'}
                      <span className="text-xs text-slate-400 block mt-0.5">
                        {item.created_at ? format(new Date(item.created_at), "h:mm a") : ''}
                      </span>
                    </TableCell>
                    <TableCell className="text-right pr-4">
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <Button variant="ghost" size="icon" onClick={() => handleView(item.id)} className="h-8 w-8 text-slate-400 hover:text-primary">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(item.id)} className="h-8 w-8 text-slate-400 hover:text-primary">
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-primary">
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => window.open(`${import.meta.env.VITE_BACKEND_URL}/rfqs/${item.id}/pdf`, '_blank')}>
                              <Download className="w-4 h-4 mr-2" /> Export PDF
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => handleDelete(item.id)}>
                              <Trash2 className="w-4 h-4 mr-2" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete RFQ ID {rfqToDelete}.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setRfqToDelete(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      {/* PREVIEW STATE */}
      <DocumentPreviewDialog
        open={previewOpen}
        onOpenChange={setPreviewOpen}
        title={previewContent?.title || "RFQ Preview"}
        type="text"
        textContent={previewContent?.content || "Loading..."}
        onDownload={() => previewContent && window.open(`${import.meta.env.VITE_BACKEND_URL}/rfqs/${previewContent.id}/pdf`, '_blank')}
      />
    </MainLayout>
  );
}
