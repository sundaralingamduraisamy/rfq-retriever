import { useState, useEffect, useRef } from 'react';
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
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Image as ImageIcon
} from 'lucide-react';
import { toast } from 'sonner';
import { MainLayout } from '@/components/layout/MainLayout';
import { DocumentPreviewDialog } from '@/components/common/DocumentPreviewDialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
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
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

import { API_BASE_URL, uploadDocument, deleteDocument } from '@/api';

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
  hasAutomobileImages?: boolean;
  hasNonAutomobileImages?: boolean;
  imageCount?: number;
}

export default function DocumentLibrary() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All Categories');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingFileName, setUploadingFileName] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [docToDelete, setDocToDelete] = useState<Document | null>(null);
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [category, setCategory] = useState('General');

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

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Store file and show category dialog
    setPendingFile(file);
    setCategoryDialogOpen(true);
  };

  const handleCategorySubmit = async () => {
    if (!pendingFile) return;

    try {
      setUploading(true);
      setUploadProgress(0);
      setUploadingFileName(pendingFile.name);
      setCategoryDialogOpen(false);

      const formData = new FormData();
      formData.append('file', pendingFile);
      formData.append('category', category);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE_URL}/upload`);

      let interval: any;

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          // Phase 1: Uploading (Cap at 90%)
          const percentComplete = Math.round((event.loaded / event.total) * 90);
          setUploadProgress(percentComplete);

          if (percentComplete >= 90) {
            // Once upload is basically done, start a slow simulation for processing (Phase 2)
            if (!interval) {
              setUploadingFileName(prev => `${prev} (Indexing...)`);
              interval = setInterval(() => {
                setUploadProgress(prev => {
                  if (prev < 98) return prev + 1;
                  return prev;
                });
              }, 800);
            }
          }
        }
      };

      const resultPromise = new Promise((resolve, reject) => {
        xhr.onload = () => {
          if (interval) clearInterval(interval);
          if (xhr.status >= 200 && xhr.status < 300) {
            setUploadProgress(100);
            resolve(JSON.parse(xhr.responseText));
          } else {
            try {
              const errorData = JSON.parse(xhr.responseText);
              reject(new Error(errorData.detail || 'Upload failed'));
            } catch (e) {
              reject(new Error('Upload failed'));
            }
          }
        };
        xhr.onerror = () => {
          if (interval) clearInterval(interval);
          reject(new Error('Network error during upload'));
        };
      });

      xhr.send(formData);
      const result: any = await resultPromise;
      const stats = result.image_stats;

      // Show success toast with color indicators
      toast.success("Document Uploaded Successfully", {
        description: (
          <div className="mt-2 space-y-2">
            <p className="text-xs text-muted-foreground">{pendingFile.name} has been processed.</p>
            <div className="flex gap-4">
              {stats?.has_automobile && (
                <div className="flex items-center gap-1 text-green-600 font-medium text-xs">
                  <CheckCircle2 className="w-3 h-3" /> Automobile Images Detected
                </div>
              )}
              {stats?.has_non_automobile && (
                <div className="flex items-center gap-1 text-red-600 font-medium text-xs">
                  <XCircle className="w-3 h-3" /> Non-Automobile Images Found
                </div>
              )}
              {!stats?.has_automobile && !stats?.has_non_automobile && (
                <div className="text-xs text-muted-foreground">No images found in document.</div>
              )}
            </div>
          </div>
        ),
        duration: 5000,
      });

      // Refresh list
      await fetchDocuments();
    } catch (error) { // eslint-disable-next-line
      alert("Upload failed: " + (error as any).message);
    } finally {
      setUploading(false);
      setUploadProgress(0);
      setUploadingFileName('');
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  /* PREVIEW STATE */
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);
  const [previewText, setPreviewText] = useState<string>("");

  const handleView = async (doc: Document) => {
    setPreviewDoc(doc);
    if (doc.type !== 'pdf') {
      // Fetch text for preview
      try {
        const res = await fetch(`${API_BASE_URL}/rfq_text/${encodeURIComponent(doc.name)}`);
        if (res.ok) {
          const data = await res.json();
          setPreviewText(data.text);
        } else {
          setPreviewText("Failed to load text content.");
        }
      } catch (e) {
        setPreviewText("Error loading content.");
      }
    }
    setPreviewOpen(true);
  };

  const handleDownload = (doc: Document) => {
    window.open(`${API_BASE_URL}/documents/${doc.id}/download`, '_blank');
  };


  const handleDelete = (doc: Document) => {
    setDocToDelete(doc);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!docToDelete) return;

    try {
      await deleteDocument(docToDelete.id);
      await fetchDocuments();
    } catch (error) { // eslint-disable-next-line
      alert("Delete failed: " + (error as any).message);
    } finally {
      setDeleteDialogOpen(false);
      setDocToDelete(null);
    }
  };

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
          <Button className="gap-2" onClick={handleUploadClick} disabled={uploading}>
            <Upload className="w-4 h-4" />
            {uploading ? "Uploading..." : "Upload Document"}
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".pdf,.doc,.docx"
          />
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
              <div className="rounded-xl border border-slate-200 bg-white shadow-soft-sm overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50/50 border-b border-slate-100">
                      <TableHead className="w-[400px] pl-6 py-4 text-xs font-semibold uppercase tracking-wider text-slate-500">Document Name</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-500">Category</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-500">Size</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-500">Uploaded</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {uploading && (
                      <TableRow className="bg-primary/5 animate-pulse">
                        <TableCell className="pl-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                              <RefreshCw className="w-4 h-4 text-primary animate-spin" />
                            </div>
                            <div className="flex flex-col gap-1 flex-1 min-w-[200px]">
                              <span className="font-medium text-primary flex items-center gap-2">
                                {uploadingFileName}
                                <span className="text-[10px] bg-primary/10 px-1.5 py-0.5 rounded text-primary uppercase font-bold tracking-wider">Uploading...</span>
                              </span>
                              <div className="flex items-center gap-3">
                                <Progress value={uploadProgress} className="h-1.5 flex-1" />
                                <span className="text-[10px] font-mono font-bold text-primary w-8">{uploadProgress}%</span>
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-100 text-slate-400 text-xs font-medium border border-slate-200 uppercase tracking-tighter italic">
                            {category}
                          </span>
                        </TableCell>
                        <TableCell className="text-slate-400 text-sm font-mono italic">
                          - KB
                        </TableCell>
                        <TableCell className="text-slate-400 text-sm italic">
                          Just now
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    )}
                    {filteredDocs.map((doc, index) => {
                      const Icon = fileIcons[doc.type] || fileIcons.unknown;
                      return (
                        <TableRow
                          key={doc.id}
                          className={cn(
                            'group hover:bg-slate-50/80 transition-colors border-b border-slate-50 last:border-0'
                          )}
                          style={{ animationDelay: `${index * 30}ms` }}
                        >
                          <TableCell className="pl-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className={cn("p-2 rounded-lg bg-slate-50 border border-slate-100", fileColors[doc.type] && 'bg-opacity-10')}>
                                <Icon
                                  className={cn('w-4 h-4', fileColors[doc.type] || fileColors.unknown)}
                                />
                              </div>
                              <span className="font-medium text-slate-700">{doc.name}</span>
                              {doc.hasAutomobileImages && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-green-50 text-green-600 border border-green-100">
                                  <CheckCircle2 className="w-2.5 h-2.5" />
                                  VISION ({doc.imageCount})
                                </span>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-100 text-slate-600 text-xs font-medium border border-slate-200">
                              {doc.category}
                            </span>
                          </TableCell>
                          <TableCell className="text-slate-500 text-sm font-mono">
                            {(doc.size / 1024).toFixed(1)} KB
                          </TableCell>
                          <TableCell className="text-slate-500 text-sm">
                            {format(new Date(doc.uploadedAt), 'MMM d, yyyy')}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-primary">
                                  <MoreVertical className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleView(doc)}>
                                  <Eye className="w-4 h-4 mr-2" />
                                  View
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleDownload(doc)}>
                                  <Download className="w-4 h-4 mr-2" />
                                  Download
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive focus:text-destructive"
                                  onClick={() => handleDelete(doc)}
                                >
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
                {uploading && (
                  <div className="group relative rounded-xl bg-primary/5 border border-primary/20 p-5 shadow-soft-sm animate-pulse">
                    <div className="flex items-start justify-between mb-4">
                      <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                        <RefreshCw className="w-6 h-6 text-primary animate-spin" />
                      </div>
                    </div>
                    <p className="font-semibold text-sm text-primary truncate mb-2">
                      {uploadingFileName}
                    </p>
                    <div className="space-y-2">
                      <div className="flex justify-between text-[10px] font-bold text-primary uppercase tracking-wider">
                        <span>Uploading</span>
                        <span>{uploadProgress}%</span>
                      </div>
                      <Progress value={uploadProgress} className="h-1.5" />
                    </div>
                  </div>
                )}
                {filteredDocs.map((doc, index) => {
                  const Icon = fileIcons[doc.type] || fileIcons.unknown;
                  return (
                    <div
                      key={doc.id}
                      className={cn(
                        'group relative rounded-xl bg-white border border-slate-200 p-5',
                        'shadow-soft-sm hover:shadow-soft-md hover:border-primary/20 hover:-translate-y-0.5 transition-all duration-300',
                        'animate-fade-in cursor-pointer'
                      )}
                      style={{ animationDelay: `${index * 30}ms` }}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className={cn("p-3 rounded-lg bg-slate-50 border border-slate-100 group-hover:bg-blue-50/50 group-hover:border-blue-100 transition-colors")}>
                          <Icon className={cn('w-6 h-6', fileColors[doc.type] || fileColors.unknown)} />
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-slate-400 opacity-0 group-hover:opacity-100 transition-all hover:text-primary"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleView(doc)}>
                              <Eye className="w-4 h-4 mr-2" /> View
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleDownload(doc)}>
                              <Download className="w-4 h-4 mr-2" /> Download
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-destructive focus:text-destructive"
                              onClick={() => handleDelete(doc)}
                            >
                              <Trash2 className="w-4 h-4 mr-2" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                      <p className="font-semibold text-sm text-slate-800 truncate mb-1" title={doc.name}>
                        {doc.name}
                      </p>
                      {doc.hasAutomobileImages && (
                        <div className="flex items-center gap-1 mb-1.5">
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-green-50 text-green-600 border border-green-100">
                            <CheckCircle2 className="w-2.5 h-2.5" />
                            VISION ({doc.imageCount})
                          </span>
                        </div>
                      )}
                      <div className="flex items-center justify-between text-xs">
                        <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-medium">
                          {doc.category}
                        </span>
                        <span className="text-slate-400 font-mono">
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
        {!loading && filteredDocs.length === 0 && !uploading && (
          <div className="flex flex-col items-center justify-center py-16 text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="w-16 h-16 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-4 shadow-soft-sm">
              <FolderOpen className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">No documents found</h3>
            <p className="text-sm text-slate-500 max-w-sm mb-6 leading-relaxed">
              Try adjusting your search or filters, or upload new documents to
              your knowledge base.
            </p>
            <Button onClick={handleUploadClick} variant="outline" className="shadow-sm border-slate-200">
              <Upload className="w-4 h-4 mr-2" />
              Upload Document
            </Button>
          </div>
        )}

        {/* Uploading State for Empty Library */}
        {!loading && filteredDocs.length === 0 && uploading && (
          <div className="flex flex-col items-center justify-center py-24 text-center animate-in fade-in duration-500">
            <div className="w-20 h-20 rounded-3xl bg-primary/10 border-2 border-primary/20 flex items-center justify-center mb-8 relative shadow-lg shadow-primary/5">
              <RefreshCw className="w-10 h-10 text-primary animate-spin" />
              <div className="absolute -bottom-2 -right-2 bg-primary text-white text-[10px] font-black px-2 py-1 rounded-full shadow-md uppercase tracking-tighter">
                {uploadProgress}%
              </div>
            </div>
            <h3 className="text-2xl font-black text-slate-900 mb-2 tracking-tight">Uploading Document...</h3>
            <p className="text-slate-500 text-sm mb-8 font-medium">
              Processing <span className="text-primary font-bold">{uploadingFileName}</span> and analyzing technical content.
            </p>
            <div className="w-full max-w-md space-y-3 bg-white p-6 rounded-2xl border border-slate-100 shadow-soft-lg">
              <div className="flex justify-between text-xs font-bold uppercase text-slate-400 tracking-widest">
                <span>Upload Status</span>
                <span className="text-primary">{uploadProgress}% Complete</span>
              </div>
              <Progress value={uploadProgress} className="h-3 shadow-inner" />
              <p className="text-[11px] text-slate-400 font-medium italic">
                Please don't close this tab while your document is being indexed.
              </p>
            </div>
          </div>
        )}
      </div>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete
              <span className="font-semibold text-foreground"> {docToDelete?.name} </span>
              from the document library.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDocToDelete(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Category Dialog */}
      <AlertDialog open={categoryDialogOpen} onOpenChange={setCategoryDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Upload Document</AlertDialogTitle>
            <AlertDialogDescription>
              Select a category/department for this document
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Design">Design</SelectItem>
                <SelectItem value="Safety">Safety</SelectItem>
                <SelectItem value="Quality">Quality</SelectItem>
                <SelectItem value="Manufacturing">Manufacturing</SelectItem>
                <SelectItem value="General">General</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setPendingFile(null);
              setCategory('General');
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleCategorySubmit}>
              Upload
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Preview Dialog */}
      <DocumentPreviewDialog
        open={previewOpen}
        onOpenChange={setPreviewOpen}
        title={previewDoc?.name || "Document Preview"}
        type={previewDoc?.type === 'pdf' ? 'pdf' : 'text'}
        previewUrl={previewDoc ? `${API_BASE_URL}/documents/${previewDoc.id}/view` : undefined}
        textContent={previewText}
        onDownload={previewDoc ? () => handleDownload(previewDoc) : undefined}
      />
    </MainLayout>
  );
}
