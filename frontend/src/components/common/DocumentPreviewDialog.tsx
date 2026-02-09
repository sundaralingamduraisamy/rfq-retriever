import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RFQMarkdown } from "./RFQMarkdown";

interface DocumentPreviewDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title: string;
    type: 'pdf' | 'text' | 'unknown';
    previewUrl?: string; // For PDFs
    textContent?: string; // For DOCX/Text
    onDownload?: () => void;
}

export function DocumentPreviewDialog({
    open,
    onOpenChange,
    title,
    type,
    previewUrl,
    textContent,
    onDownload
}: DocumentPreviewDialogProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-0 gap-0">
                <DialogHeader className="px-6 py-4 border-b flex flex-row items-center justify-between space-y-0">
                    <DialogTitle className="text-xl font-semibold truncate max-w-[calc(100%-100px)]" title={title}>
                        {title}
                    </DialogTitle>
                    <div className="flex items-center gap-2">
                        {onDownload && (
                            <Button size="sm" variant="outline" onClick={onDownload}>
                                <Download className="w-4 h-4 mr-2" />
                                Download
                            </Button>
                        )}
                    </div>
                </DialogHeader>

                <div className="flex-1 bg-muted/10 overflow-hidden relative">
                    {type === 'pdf' && previewUrl ? (
                        <iframe
                            src={previewUrl}
                            className="w-full h-full border-0"
                            title="Document Preview"
                        />
                    ) : type === 'text' && textContent ? (
                        <ScrollArea className="h-full">
                            <div className="p-8 max-w-4xl mx-auto bg-white min-h-full shadow-lg my-4 rounded-xl border border-slate-100">
                                <RFQMarkdown content={textContent} />
                            </div>
                        </ScrollArea>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                            <p>Preview not available for this file type.</p>
                            {onDownload && (
                                <Button variant="link" onClick={onDownload} className="mt-2">
                                    Download to view
                                </Button>
                            )}
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
