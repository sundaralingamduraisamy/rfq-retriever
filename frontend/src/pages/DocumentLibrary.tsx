import { useState, useEffect } from 'react';
import {
  Search,
  Upload,
  FileText,
  FileSpreadsheet,
  File,
  MoreVertical,
  Download,
  Trash2,
  Eye,
  FolderOpen,
  Grid,
  List,
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { API_BASE_URL } from '@/api';

const fileIcons: Record<string, any> = {
  pdf: FileText,
  docx: File,
  xlsx: FileSpreadsheet,
  unknown: File,
};

const fileColors: Record<string, string> = {
  pdf: 'text-destructive',
  docx: 'text-primary',
  xlsx: 'text-success',
  unknown: 'text-muted-foreground',
};

interface Document {
  id: string;
  name: string;
  type: string;
  category: string;
  size: number;
  uploadedAt: string;
  relevanceScore: number;
}

export default function DocumentLibrary() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All Categories');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (error) {
      console.error("Failed to fetch documents:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesCategory =
      categoryFilter === 'All Categories' || doc.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  // Calculate stats
  const totalDocs = documents.length;
  // Get unique categories from actual data
  const categories = ['All Categories', ...new Set(documents.map(d => d.category))];
  const uniqueCategoriesCount = categories.length - 1; // Subtract 'All Categories'

  return (
    <MainLayout>
      <div className="p-6 lg:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Document Library</h1>
            <p className="text-muted-foreground mt-1">
              Manage your knowledge base of historical RFQs and templates
            </p>
          </div>
          <Button className="gap-2">
            <Upload className="w-4 h-4" />
            Upload Document
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="rounded-xl bg-card border border-border p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{loading ? "..." : totalDocs}</p>
                <p className="text-sm text-muted-foreground">Total Documents</p>
              </div>
            </div>
          </div>
          <div className="rounded-xl bg-card border border-border p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10">
                <FolderOpen className="w-5 h-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold">{loading ? "..." : uniqueCategoriesCount}</p>
                <p className="text-sm text-muted-foreground">Categories</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              {categories.map((category) => (
                <SelectItem key={category} value={category}>
                  {category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-1 p-1 rounded-lg bg-muted">
            <Button
              variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-8 w-8"
              onClick={() => setViewMode('grid')}
            >
              <Grid className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-8 w-8"
              onClick={() => setViewMode('list')}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <p className="text-muted-foreground">Loading documents...</p>
          </div>
        )}

        {/* Document List/Grid */}
        {!loading && (
          <>
            {viewMode === 'list' ? (
              <div className="rounded-xl border border-border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/30">
                      <TableHead className="w-[400px]">Name</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Uploaded</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredDocs.map((doc, index) => {
                      const Icon = fileIcons[doc.type] || fileIcons.unknown;
                      return (
                        <TableRow
                          key={doc.id}
                          className={cn(
                            'hover:bg-muted/30 animate-fade-in'
                          )}
                          style={{ animationDelay: `${index * 30}ms` }}
                        >
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <div className="p-2 rounded-lg bg-muted">
                                <Icon
                                  className={cn('w-5 h-5', fileColors[doc.type] || fileColors.unknown)}
                                />
                              </div>
                              <span className="font-medium">{doc.name}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="px-2 py-1 rounded-md bg-muted text-xs">
                              {doc.category}
                            </span>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {(doc.size / 1024).toFixed(1)} KB
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {format(new Date(doc.uploadedAt), 'MMM d, yyyy')}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreVertical className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Eye className="w-4 h-4 mr-2" />
                                  View
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <Download className="w-4 h-4 mr-2" />
                                  Download
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem className="text-destructive">
                                  <Trash2 className="w-4 h-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {filteredDocs.map((doc, index) => {
                  const Icon = fileIcons[doc.type] || fileIcons.unknown;
                  return (
                    <div
                      key={doc.id}
                      className={cn(
                        'group rounded-xl bg-card border border-border p-4',
                        'hover:border-primary/30 transition-all duration-200',
                        'animate-fade-in cursor-pointer'
                      )}
                      style={{ animationDelay: `${index * 30}ms` }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="p-3 rounded-lg bg-muted">
                          <Icon className={cn('w-8 h-8', fileColors[doc.type] || fileColors.unknown)} />
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Eye className="w-4 h-4 mr-2" />
                              View
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Download className="w-4 h-4 mr-2" />
                              Download
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive">
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                      <p className="font-medium text-sm truncate mb-1">{doc.name}</p>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{doc.category}</span>
                        <span className="text-muted-foreground font-medium">
                          {(doc.size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* Empty State */}
        {!loading && filteredDocs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mb-4">
              <FolderOpen className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No documents found</h3>
            <p className="text-sm text-muted-foreground max-w-sm mb-6">
              Try adjusting your search or filters, or upload new documents to
              your knowledge base.
            </p>
            <Button>
              <Upload className="w-4 h-4 mr-2" />
              Upload Document
            </Button>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
