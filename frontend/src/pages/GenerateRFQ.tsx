import { useState, useCallback, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { saveRfq, getRfqDetail } from '@/api';
import { Trash2, Edit2, Check, X, File, FileText, Download, RefreshCw, Zap, User, Bot, Save } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatInterface } from '@/components/generator/ChatInterface';
import { RFQPreview } from '@/components/generator/RFQPreview';
import {
  ChatMessage,
  AgentState,
} from '@/data/mockData';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

const BACKEND = import.meta.env.VITE_BACKEND_URL;

type RetrievedRFQ = {
  file: string;
  score: number;
  preview?: string;
};

export default function GenerateRFQ() {
  const location = useLocation();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      role: 'assistant',
      content:
        "Hello! I'm ready to help you create a professional RFQ. What would you like to build today?",
      timestamp: new Date().toISOString(),
    },
  ]);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('rfq_chat_messages');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed);
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('rfq_chat_messages', JSON.stringify(messages));
  }, [messages]);

  const [agentState, setAgentState] = useState<AgentState>({
    phase: 'idle',
    progress: 0,
  });

  const [isGenerating, setIsGenerating] = useState(false);

  const [retrievedRFQs, setRetrievedRFQs] = useState<RetrievedRFQ[]>([]);
  const [selectedRFQ, setSelectedRFQ] = useState<string | null>(null);
  const [referenceText, setReferenceText] = useState<string | null>(null);

  // DRAFTING STATE
  const [draftText, setDraftText] = useState<string>(() => {
    // If explicit navigation, wait for fetch (or start empty)
    if (location.state?.rfqId) return "";
    // Otherwise restore from storage
    return localStorage.getItem('rfq_draft_text') || "# New RFQ Spec\n\nStart typing or ask the Agent to generate content...";
  });

  const [draftMode, setDraftMode] = useState<'agent' | 'manual'>('agent');
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");

  const [rfqId, setRfqId] = useState<number | null>(() => {
    if (location.state?.rfqId) return location.state.rfqId;
    const saved = localStorage.getItem('rfq_active_id');
    return saved ? Number(saved) : null;
  });

  // PERSISTENCE EFFECTS
  useEffect(() => {
    localStorage.setItem('rfq_draft_text', draftText);
  }, [draftText]);

  useEffect(() => {
    if (rfqId) {
      localStorage.setItem('rfq_active_id', rfqId.toString());
    } else {
      localStorage.removeItem('rfq_active_id');
    }
  }, [rfqId]);

  // Load RFQ if editing (Explicit Navigation)
  useEffect(() => {
    if (location.state?.rfqId) {
      setRfqId(location.state.rfqId);
      getRfqDetail(location.state.rfqId).then(data => {
        setDraftText(data.content || "");
        setAgentState({ phase: 'draft', progress: 100 });
      }).catch(err => console.error(err));
    }
  }, [location.state]);

  const handleSave = async () => {
    try {
      setSaveStatus("saving");
      const title = draftText.split('\n')[0].replace('#', '').trim() || "Untitled RFQ";
      const res = await saveRfq({
        id: rfqId,
        title: title.substring(0, 50),
        content: draftText,
        status: "draft"
      });
      setRfqId(res.id);
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch (e) {
      alert("Failed to save draft");
      setSaveStatus("idle");
    }
  };

  const handleResetSession = () => {
    if (confirm("Are you sure? This will clear the current draft and chat history.")) {
      setMessages([{
        id: 'msg-init-new',
        role: 'assistant',
        content: "Session reset. I'm ready to help you create a professional RFQ. What would you like to build today?",
        timestamp: new Date().toISOString(),
      }]);
      setDraftText("# New RFQ Spec\n\n");
      setRetrievedRFQs([]);
      setSelectedRFQ(null);
      setReferenceText(null);
      setRfqId(null); // Reset RFQ ID
      localStorage.removeItem('rfq_chat_messages');
      localStorage.removeItem('rfq_draft_text');
      localStorage.removeItem('rfq_active_id');
    }
  };

  const handleSendMessage = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        id: `msg-user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsGenerating(true);
      setAgentState({ phase: 'retrieve', progress: 20 });

      try {
        const history = messages.map(m => ({
          role: m.role === 'assistant' ? 'agent' : 'user',
          text: m.content
        }));

        const response = await fetch(`${BACKEND}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_message: content,
            history: history,
            current_draft: draftText,
            mode: draftMode
          }),
        });

        const data = await response.json();
        setAgentState({ phase: 'draft', progress: 60 });

        // Update Documents
        if (data.related_documents && data.related_documents.length > 0) {
          setRetrievedRFQs(data.related_documents);
        }

        // Update Draft (If Agent Edited)
        if (data.updated_draft) {
          setDraftText(data.updated_draft);
        }

        // Add LLM response to messages
        const assistantMsgs: ChatMessage[] = [];

        assistantMsgs.push({
          id: `msg-assistant-${Date.now()}`,
          role: 'assistant',
          content: data.reply,
          timestamp: new Date().toISOString(),
          sources: data.related_documents ? data.related_documents.map((d: any) => ({
            name: d.file || d.name,
            relevance: d.score || d.relevanceScore,
            type: (d.file || d.name || '').endsWith('.pdf') ? 'pdf' : 'docx'
          })) : undefined
        });

        // Add Impact Analysis if present
        if (data.impact_analysis) {
          assistantMsgs.push({
            id: `msg-impact-${Date.now()}`,
            role: 'assistant',
            content: `**Impact Analysis:**\n\n${data.impact_analysis}`,
            timestamp: new Date().toISOString(),
          });
        }

        setMessages((prev) => [...prev, ...assistantMsgs]);

      } catch (error) {
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-error-${Date.now()}`,
            role: 'assistant',
            content: 'Error communicating with the assistant. Please try again.',
            timestamp: new Date().toISOString(),
          },
        ]);
      } finally {
        setIsGenerating(false);
        setAgentState({ phase: 'idle', progress: 0 });
      }
    },
    [messages, draftText, draftMode]
  );

  const handleDocumentSelect = async (filename: string) => {
    setSelectedRFQ(filename);
    try {
      // If it's a PDF, we don't strictly need text for preview but good for context
      // If it's Word/Text, we fetch text
      const res = await fetch(`${BACKEND}/rfq_text/${encodeURIComponent(filename)}`);
      const data = await res.json();
      setReferenceText(data.text);
    } catch (e) {
      console.error("Failed to fetch document text", e);
    }
  };

  const handleExport = async () => {
    if (!draftText) return;

    const res = await fetch(`${BACKEND}/export/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: draftText }),
    });

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'RFQ.pdf';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <MainLayout>
      <div className="h-[calc(100vh-4rem)] flex flex-col overflow-hidden">
        {/* --- Main Toolbar --- */}
        <div className="border-b border-border bg-card p-3 flex items-center justify-between shadow-sm z-50 sticky top-0">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">RFQ Generator Mode</h1>
            <div className="h-6 w-px bg-border"></div>
            <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-md">
              <Button
                variant={draftMode === 'manual' ? 'secondary' : 'ghost'}
                size="sm"
                className="h-7 px-3 text-xs"
                onClick={() => setDraftMode('manual')}
              >
                <User className="w-3 h-3 mr-1" /> Manual
              </Button>
              <Button
                variant={draftMode === 'agent' ? 'secondary' : 'ghost'}
                size="sm"
                className="h-7 px-3 text-xs"
                onClick={() => setDraftMode('agent')}
              >
                <Bot className="w-3 h-3 mr-1" /> Agent
              </Button>
            </div>
            {draftMode === 'agent' && <Badge variant="secondary" className="text-xs text-blue-600"><Zap className="w-3 h-3 mr-1 fill-blue-500" /> Auto-Edit Active</Badge>}
          </div>

          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={handleResetSession} className="text-red-500 hover:text-red-600 hover:bg-red-50">
              <RefreshCw className="w-4 h-4 mr-2" /> New RFQ
            </Button>
            <Button size="sm" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" /> Export PDF
            </Button>
          </div>
        </div>

        <ResizablePanelGroup direction="horizontal" className="flex-1 overflow-hidden">
          {/* --- LEFT PANEL: CHAT & DOCS --- */}
          <ResizablePanel defaultSize={40} minSize={30}>
            <div className="h-full flex flex-col border-r border-border bg-background">



              <div className="flex-1 overflow-hidden">
                <ChatInterface
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  agentState={agentState}
                  isGenerating={isGenerating}
                  onSourceClick={handleDocumentSelect} // Keep for inline citations
                />
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle />

          {/* --- RIGHT PANEL: EDITOR / PREVIEW --- */}
          <ResizablePanel defaultSize={60} minSize={30}>
            <div className="h-full bg-card flex flex-col">
              <div className="flex items-center justify-between border-b border-border p-3 bg-muted/20">
                <span className="font-semibold text-sm flex items-center gap-2">
                  {rfqId ? <Badge variant="outline" className="text-xs">ID: {rfqId}</Badge> : null}
                  Draft Editor
                </span>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={handleSave} disabled={saveStatus === "saving"}>
                    <Save className="w-4 h-4 mr-2" />
                    {saveStatus === "saving" ? "Saving..." : saveStatus === "saved" ? "Saved" : "Save"}
                  </Button>
                </div>
              </div>

              {selectedRFQ && (
                <div className="flex-shrink-0 bg-muted/30 border-b border-border p-2 flex items-center justify-between">
                  <span className="text-sm font-medium flex items-center gap-2">
                    <File className="w-4 h-4" /> Viewing: {selectedRFQ}
                  </span>
                  <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => setSelectedRFQ(null)}>
                    <X className="w-3 h-3 mr-1" /> Close Preview
                  </Button>
                </div>
              )}

              <div className="flex-1 overflow-hidden relative">
                {selectedRFQ ? (
                  /* Document Preview Mode */
                  selectedRFQ.toLowerCase().endsWith('.pdf') ? (
                    <iframe
                      src={`${BACKEND}/documents/${selectedRFQ}/view`}
                      className="w-full h-full border-0"
                      title="Preview"
                    />
                  ) : (
                    <div className="p-8 h-full overflow-y-auto bg-white">
                      <pre className="whitespace-pre-wrap font-sans text-sm">{referenceText || "Loading..."}</pre>
                    </div>
                  )
                ) : (
                  /* Persistent Draft Editor */
                  <textarea
                    className={`w-full h-full p-8 resize-none focus:outline-none font-mono text-sm leading-relaxed transition-colors ${draftMode === 'agent' ? 'bg-muted/5' : 'bg-background'}`}
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    placeholder="# Start your RFQ here..."
                  />
                )}

                {/* Floating Action for selected doc (optional) */}
                {selectedRFQ && referenceText && (
                  <div className="absolute bottom-4 right-4 shadow-lg">
                    <Button size="sm" onClick={() => {
                      setDraftText(referenceText);
                      setSelectedRFQ(null);
                    }}>
                      Replace Draft with This
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>

    </MainLayout>
  );
}
