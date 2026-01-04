import { useState, useCallback } from 'react';
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

const BACKEND = import.meta.env.VITE_BACKEND_URL;

type RetrievedRFQ = {
  file: string;
  score: number;
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

  const [agentState, setAgentState] = useState<AgentState>({
    phase: 'idle',
    progress: 0,
  });

  const [isGenerating, setIsGenerating] = useState(false);

  const [validated, setValidated] = useState(false);
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

      // -------------------------------------------------------------
      // 1. IF DRAFT EXISTS -> TREAT AS AI EDIT INSTRUCTION
      // -------------------------------------------------------------
      if (draftText && validated) {
        try {
          // Temporarily show that we are analyzing/updating
          setAgentState({ phase: 'analyze', progress: 50 });

          const editRes = await fetch(`${BACKEND}/edit_rfq`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              current_text: draftText,
              instruction: content,
            }),
          });
          const editData = await editRes.json();

          setDraftText(editData.updated_text);

          setMessages((prev) => [
            ...prev,
            {
              id: `msg-edit-${Date.now()}`,
              role: 'assistant',
              content: `**Impact Analysis:**\n\n${editData.analysis}`,
              timestamp: new Date().toISOString(),
            },
          ]);
        } catch (e) {
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-err-${Date.now()}`,
              role: 'assistant',
              content: 'Failed to update RFQ. Please try again.',
              timestamp: new Date().toISOString(),
            },
          ]);
        } finally {
          setIsGenerating(false);
          setAgentState({ phase: 'idle', progress: 0 });
        }
        return;
      }

      // -------------------------------------------------------------
      // 2. STANDARD FLOW (VALIDATION & SEARCH)
      // -------------------------------------------------------------
      try {
        const validateRes = await fetch(`${BACKEND}/validate_requirement`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ requirement: content }),
        });

        const validateData = await validateRes.json();

        if (!validateData.valid) {
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-invalid-${Date.now()}`,
              role: 'assistant',
              content: validateData.message,
              timestamp: new Date().toISOString(),
            },
          ]);
          setIsGenerating(false);
          return;
        }

        setValidated(true);

        setMessages((prev) => [
          ...prev,
          {
            id: `msg-valid-${Date.now()}`,
            role: 'assistant',
            content:
              'Your requirement is valid. Retrieving the most relevant RFQs.',
            timestamp: new Date().toISOString(),
          },
        ]);

        const searchRes = await fetch(`${BACKEND}/search_rfq`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: content }),
        });

        const searchData = await searchRes.json();
        setRetrievedRFQs(searchData.results || []);
        setReferenceText(null);
        setDraftText(null);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-error-${Date.now()}`,
            role: 'assistant',
            content:
              'Error occurred while processing the requirement. Please try again.',
            timestamp: new Date().toISOString(),
          },
        ]);
      } finally {
        setIsGenerating(false);
        setAgentState({ phase: 'idle', progress: 0 });
      }
    },
    [draftText, validated]
  );

  const handleDraftRFQ = async () => {
    if (!selectedRFQ) return;

    setIsGenerating(true);
    setAgentState({ phase: 'draft', progress: 50 });

    try {
      const res = await fetch(`${BACKEND}/generate_final_rfq`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement: messages[messages.length - 1].content,
          filled_data: {},
          reference_file: selectedRFQ,
        }),
      });

      const data = await res.json();
      setDraftText(data.draft);

      setMessages((prev) => [
        ...prev,
        {
          id: `msg-drafted-${Date.now()}`,
          role: 'assistant',
          content:
            'The RFQ has been drafted. You can now:\n1. Click **Edit** to manually modify text.\n2. **Chat** below to instruct me to make changes (e.g., "Add payment terms").\n\nI will analyze all changes automatically.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-draft-error-${Date.now()}`,
          role: 'assistant',
          content:
            'Failed to generate RFQ draft. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsGenerating(false);
      setAgentState({ phase: 'idle', progress: 0 });
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
                />
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle />

          <ResizablePanel defaultSize={50} minSize={35}>
            <div className="h-full bg-card/30 p-6 overflow-y-auto">
              {validated && retrievedRFQs.length > 0 && !draftText && (
                <>
                  <h2 className="text-lg font-semibold mb-4">
                    Select Reference RFQ
                  </h2>

                  <div className="space-y-3">
                    {retrievedRFQs.map((rfq) => (
                      <div
                        key={rfq.file}
                        className={`border rounded-lg p-4 cursor-pointer ${selectedRFQ === rfq.file
                            ? 'border-primary bg-primary/5'
                            : 'bg-card'
                          }`}
                        onClick={async () => {
                          setSelectedRFQ(rfq.file);
                          setDraftText(null);

                          const res = await fetch(
                            `${BACKEND}/rfq_text/${encodeURIComponent(rfq.file)}`
                          );
                          const data = await res.json();
                          setReferenceText(data.text);
                        }}
                      >
                        <p className="font-mono text-sm">{rfq.file}</p>
                        <p className="text-xs text-muted-foreground">
                          Relevance: {rfq.score.toFixed(2)}
                        </p>
                      </div>
                    ))}
                  </div>

                  <Button
                    className="mt-6"
                    disabled={!selectedRFQ}
                    onClick={handleDraftRFQ}
                  >
                    Draft RFQ
                  </Button>
                </>
              )}

              {selectedRFQ && referenceText && !draftText && (
                <RFQPreview isVisible={true} content={referenceText} />
              )}

              {draftText && (
                <RFQPreview
                  isVisible={true}
                  content={draftText}
                  onExport={handleExport}
                  onEdit={() => setIsEditingMode(true)}
                  isEditing={isEditingMode}
                  onSave={handleSaveEdit}
                  onCancel={() => setIsEditingMode(false)}
                />
              )}

              {!validated && <RFQPreview isVisible={false} />}
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </MainLayout>
  );
}
