import { useState, useMemo, useEffect } from 'react';
import {
  FileText,
  Download,
  Copy,
  Edit3,
  Check,
  Save,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface RFQPreviewProps {
  isVisible: boolean;
  content?: string;
  onExport?: () => void;
  onEdit?: () => void;
  // New props for inline editing
  isEditing?: boolean;
  onSave?: (newContent: string) => void;
  onCancel?: () => void;
}

const SECTION_TITLES = [
  'BACKGROUND & OBJECTIVE',
  'SCOPE OF WORK',
  'TECHNICAL REQUIREMENTS',
  'SERVICE LEVEL AGREEMENT',
  'COMPLIANCE & STANDARDS',
  'COMMERCIAL TERMS',
  'DELIVERY TIMELINE',
  'EVALUATION CRITERIA',
  'REVISION HISTORY',
];

export function RFQPreview({
  isVisible,
  content,
  onExport,
  onEdit,
  isEditing = false,
  onSave,
  onCancel,
}: RFQPreviewProps) {
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  const [editBuffer, setEditBuffer] = useState('');

  // Sync content to buffer/sections when entering edit mode
  useEffect(() => {
    if (isEditing && content) {
      setEditBuffer(content);
      // Parse sections for editing
      const parsed = parseSections(content);
      setEditableSections(parsed);
    }
  }, [isEditing, content]);

  // Helper to parse sections (moved out or duplicated for stability)
  const parseSections = (text: string) => {
    const normalized = text.replace(/\r/g, '');
    const parts: { title: string; body: string }[] = [];

    // Create lowercased version for search to make it case-insensitive
    const lowerText = normalized.toLowerCase();
    const lowerTitles = SECTION_TITLES.map(t => t.toLowerCase());

    for (let i = 0; i < SECTION_TITLES.length; i++) {
      const title = SECTION_TITLES[i];
      const lowerTitle = lowerTitles[i];

      // Find index using lowercased text
      const start = lowerText.indexOf(lowerTitle);
      if (start === -1) continue;

      // Calculate content start based on original title length
      const contentStart = start + title.length;

      // Find next title
      let end = -1;
      if (i < SECTION_TITLES.length - 1) {
        const nextLowerTitle = lowerTitles[i + 1];
        const nextStart = lowerText.indexOf(nextLowerTitle, contentStart);
        if (nextStart !== -1) {
          end = nextStart;
        }
      }

      const body = normalized
        .substring(contentStart, end === -1 ? normalized.length : end)
        .trim();

      parts.push({ title, body });
    }
    return parts;
  };

  const [editableSections, setEditableSections] = useState<{ title: string, body: string }[]>([]);

  // Restore sections for read-only view
  const sections = useMemo(() => {
    if (!content) return [];
    return parseSections(content);
  }, [content]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(id);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const handleSectionChange = (index: number, newBody: string) => {
    const updated = [...editableSections];
    updated[index].body = newBody;
    setEditableSections(updated);
  };

  const handleSaveInternal = () => {
    // Reconstruct full text
    // We strictly follow the SECTION_TITLES order or the current editableSections order?
    // Using editableSections order preserves what we see.
    const fullText = editableSections.map(s => `${s.title}\n\n${s.body}`).join('\n\n');
    onSave?.(fullText);
  };

  if (!isVisible || !content) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8">
        <div className="w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mb-4">
          <FileText className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">No RFQ Preview</h3>
        <p className="text-sm text-muted-foreground max-w-sm">
          Select a reference RFQ or generate a draft to preview it here.
        </p>
      </div>
    );
  }

  // Display sections: if editing, use editableSections; else use memoized sections
  const displaySections = isEditing ? editableSections : sections;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h2 className="text-lg font-semibold">
          {isEditing ? 'Editing RFQ' : 'RFQ Preview'}
        </h2>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
              >
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSaveInternal}
              >
                <Save className="w-4 h-4 mr-2" />
                Save & Analyze
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={onExport}
                disabled={!onExport}
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button
                size="sm"
                onClick={onEdit}
                disabled={!onEdit}
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Edit
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-card">
        {displaySections.length > 0 ? (
          displaySections.map((section, index) => (
            <div
              key={section.title}
              className={cn(
                'rounded-xl border p-6 transition-all',
                !isEditing && selectedSection === section.title
                  ? 'border-primary bg-primary/5'
                  : 'border-border'
              )}
              onClick={() => !isEditing && setSelectedSection(section.title)}
            >
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-bold tracking-wider uppercase text-primary">
                  {section.title}
                </h3>
                {!isEditing && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy(section.title, section.body);
                    }}
                  >
                    {copiedSection === section.title ? (
                      <Check className="w-4 h-4 text-success" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                )}
              </div>

              {isEditing ? (
                <Textarea
                  value={section.body}
                  onChange={(e) => handleSectionChange(index, e.target.value)}
                  className="w-full min-h-[150px] font-sans text-sm resize-y leading-relaxed bg-muted/30 border-muted focus-visible:ring-1"
                />
              ) : (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      table: ({ node, ...props }) => (
                        <div className="my-4 w-full overflow-hidden rounded-lg border border-border shadow-sm">
                          <table className="w-full text-left text-sm" {...props} />
                        </div>
                      ),
                      thead: ({ node, ...props }) => <thead className="bg-muted/50 text-xs uppercase" {...props} />,
                      th: ({ node, ...props }) => <th className="px-4 py-2 border-b" {...props} />,
                      td: ({ node, ...props }) => <td className="px-4 py-2 border-b last:border-0" {...props} />,
                      p: ({ node, ...props }) => <p className="leading-relaxed whitespace-pre-wrap" {...props} />,
                    }}
                  >
                    {section.body}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          ))
        ) : (
          /* Fallback for unstructured content */
          isEditing ? (
            <Textarea
              value={editBuffer}
              onChange={(e) => setEditBuffer(e.target.value)}
              className="w-full h-full min-h-[500px] font-mono text-sm resize-none border-0 focus-visible:ring-0 p-0 shadow-none leading-relaxed"
            />
          ) : (
            <div className="rounded-xl border p-6">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {content}
                </ReactMarkdown>
              </div>
            </div>
          )
        )}
      </div>

      {/* Footer - Only show when not editing */}
      {!isEditing && (
        <div className="p-4 border-t border-border bg-muted/30">
          <div className="flex justify-between items-center">
            <p className="text-xs text-muted-foreground">
              Give feedback to refine (e.g., "Add a clause about recycling")
            </p>
            <Button variant="outline" size="sm" disabled>
              Update Draft
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
