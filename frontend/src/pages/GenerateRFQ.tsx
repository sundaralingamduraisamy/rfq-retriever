import { useState, useCallback, useEffect } from 'react';
import { Trash2, Edit2, Check, X, File, FileText, Download } from 'lucide-react';
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

const BACKEND = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

type RetrievedRFQ = {
  file: string;
  score: number;
  preview?: string;
};

export default function GenerateRFQ() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      role: 'assistant',
      content:
        "Hello! I'm ready to help you draft a new Request for Quotation. What would you like to create today?",
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
  const [draftText, setDraftText] = useState<string | null>(null);

  // Editing state
  const [isEditingMode, setIsEditingMode] = useState(false);

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

      try {
        // Send to /chat endpoint in the format backend expects
        // Backend wants: { user_message: string, history: Array<{role, text}> }
        const history = messages.map(m => ({
          role: m.role === 'assistant' ? 'agent' : 'user',
          text: m.content
        }));

        const response = await fetch(`${BACKEND}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_message: content,
            history: history
          }),
        });

        const data = await response.json();

        // Check for related documents
        if (data.related_documents && data.related_documents.length > 0) {
          setRetrievedRFQs(data.related_documents);
          // If docs found, clear previous selection/draft to show the list
          setSelectedRFQ(null);
          setReferenceText(null);
          setDraftText(null);
        }

        // Add LLM response to messages
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-assistant-${Date.now()}`,
            role: 'assistant',
            content: data.reply,
            timestamp: new Date().toISOString(),
          },
        ]);
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
      }
    },
    [messages]
    [messages]
  );

  const handleDocumentSelect = async (filename: string) => {
    setSelectedRFQ(filename);
    try {
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

  // ------------------------------------------------------------------
  // MANUAL EDIT HANDLER
  // ------------------------------------------------------------------
  const handleSaveEdit = async (newContent: string) => {
    if (!draftText) return;

    setIsGenerating(true);
    // Switch off edit mode immediately so UI feels responsive
    setIsEditingMode(false);
    setAgentState({ phase: 'analyze', progress: 50 });

    try {
      // Analyze the change
      const res = await fetch(`${BACKEND}/analyze_changes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          old_text: draftText,
          new_text: newContent,
        }),
      });

      const data = await res.json();
      setDraftText(newContent);

      // Post analysis to chat
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-analysis-${Date.now()}`,
          role: 'assistant',
          content: `**Manual Edit Analysis:**\n\n${data.analysis}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
      setAgentState({ phase: 'idle', progress: 0 });
    }
  };

  return (
    <MainLayout>
      <div className="h-[calc(100vh-0px)]">
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel defaultSize={50} minSize={35}>
            <div className="h-full flex flex-col border-r border-border">
              <div className="flex items-center justify-between p-4 border-b border-border">
                <div>
                  <h1 className="text-lg font-semibold">Generate RFQ</h1>
                  <p className="text-sm text-muted-foreground">
                    Describe your requirements to the AI agent
                  </p>
                </div>
              </div>

              <div className="flex-1 overflow-hidden">
                <ChatInterface
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  agentState={agentState}
                  isGenerating={isGenerating}
                  onSourceClick={handleDocumentSelect}
                />
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle />

          <ResizablePanel defaultSize={50} minSize={35}>
            <div className="h-full bg-card/30 p-6 overflow-y-auto">
              {/* Case 1: Show list of found documents */}
              {retrievedRFQs.length > 0 && !selectedRFQ && !draftText && (
                <>
                  <h2 className="text-lg font-semibold mb-4">
                    Found Documents
                  </h2>
                  <div className="space-y-3">
                    {retrievedRFQs.map((rfq) => {
                      const isPdf = rfq.file.toLowerCase().endsWith('.pdf');
                      const iconColor = isPdf ? 'text-red-500' : 'text-blue-500';
                      const bgColor = isPdf ? 'bg-red-50' : 'bg-blue-50';

                      return (
                        <div
                          key={rfq.file}
                          className="flex items-center p-3 hover:bg-muted/50 transition-colors cursor-pointer border-b border-border last:border-0"
                          onClick={() => handleDocumentSelect(rfq.file)}
                        >
                          {/* Icon Box */}
                          <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${bgColor} flex items-center justify-center mr-3`}>
                            <FileText className={`w-5 h-5 ${iconColor}`} />
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-foreground truncate" title={rfq.file}>
                              {rfq.file}
                            </p>
                          </div>

                          {/* Match Score (Subtle) */}
                          <span className="text-xs text-muted-foreground ml-2">
                            {rfq.score}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}

              {/* Case 2: Show selected reference document */}
              {selectedRFQ && referenceText && !draftText && (
                <div className="flex flex-col h-full">
                  <div className="flex items-center justify-between mb-4">
                    <Button variant="ghost" size="sm" onClick={() => setSelectedRFQ(null)}>
                      ← Back to List
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => {
                        // Draft RFQ based on this reference
                        // Trigger a new chat message to draft
                        handleSendMessage(`Please draft a new RFQ using ${selectedRFQ} as a reference.`);
                      }}
                    >
                      Draft from this
                    </Button>
                  </div>
                  <div className="flex-1 overflow-auto border rounded-md p-0 bg-background h-full">
                    {selectedRFQ.toLowerCase().endsWith('.pdf') ? (
                      <iframe
                        src={`${BACKEND}/documents/${selectedRFQ}/view`}
                        className="w-full h-full border-0"
                        title="Document Preview"
                      />
                    ) : (
                      <div className="flex flex-col h-full bg-background relative">
                        {/* Header for Editor */}
                        <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/20">
                          <span className="text-xs font-mono text-muted-foreground">{selectedRFQ}</span>
                          <div className="flex gap-2">
                            <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => window.open(`${BACKEND}/documents/${selectedRFQ}/view`, '_blank')}>
                              <Download className="w-3 h-3 mr-1" /> Original
                            </Button>
                            <Button size="sm" className="h-7 text-xs" onClick={() => {
                              setDraftText(referenceText);
                              setSelectedRFQ(null);
                            }}>
                              <FileText className="w-3 h-3 mr-1" /> Switch to Full Draft Mode
                            </Button>
                          </div>
                        </div>

                        {/* Editable Text Area (Acts as "Manual Editing") */}
                        <textarea
                          className="flex-1 w-full p-4 resize-none bg-background focus:outline-none font-mono text-sm leading-relaxed"
                          value={referenceText}
                          onChange={(e) => {
                            // "Manual Editing" Logic:
                            // If they type here, we treat it as starting a draft/edit session
                            // We update the local state. Ideally we should switch to 'draftText' mode immediately
                            // to unlock all draft features, but user wants editing "in the right side".
                            // Let's simpler: Update referenceText? No, referenceText is fetched.
                            // We should auto-promote to Draft Mode on edit.
                            setDraftText(e.target.value);
                            setSelectedRFQ(null); // This switches the VIEW to Case 3 (Draft Preview) which has the full editor
                          }}
                          placeholder="Loading document text..."
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Case 3: Show generated draft */}
              {draftText ? (
                <RFQPreview
                  isVisible={true}
                  content={draftText}
                  onExport={handleExport}
                  onEdit={() => setIsEditingMode(true)}
                  isEditing={isEditingMode}
                  onSave={handleSaveEdit}
                  onCancel={() => setIsEditingMode(false)}
                />
              ) : (
                // Case 4: Empty state (only if no list and no draft)
                !retrievedRFQs.length && (
                  <div className="flex items-center justify-center h-full text-center">
                    <div>
                      <p className="text-muted-foreground mb-2">No documents selected</p>
                      <p className="text-sm text-muted-foreground">
                        Ask the assistant to search or draft an RFQ
                      </p>
                    </div>
                  </div>
                )
              )}
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </MainLayout>
  );
}
