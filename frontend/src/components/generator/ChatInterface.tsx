import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Sparkles, FileText, RefreshCw, User as UserIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ChatMessage, AgentState } from '@/data/mockData';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { currentUser } from '@/data/mockData';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  agentState: AgentState;
  isGenerating: boolean;
  onSourceClick?: (source: string) => void;
}

const phaseLabels: Record<AgentState['phase'], string> = {
  idle: 'Ready',
  plan: 'Planning...',
  retrieve: 'Retrieving Knowledge...',
  draft: 'Drafting RFQ...',
  review: 'Reviewing...',
  analyze: 'Analyzing Impact...',
};

export function ChatInterface({
  messages,
  onSendMessage,
  agentState,
  isGenerating,
  onSourceClick,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isGenerating) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Agent State Indicator */}
      {isGenerating && (
        <div className="px-4 py-3 border-b border-border bg-muted/30 backdrop-blur-sm sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-primary animate-pulse" />
              </div>
              <div className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-primary">
                  {phaseLabels[agentState.phase] || 'Processing...'}
                </span>
              </div>
              <div className="mt-1.5 h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
                  style={{ width: `${agentState.progress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((message, index) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-4 animate-fade-in group',
              message.role === 'user' ? 'flex-row-reverse' : ''
            )}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {/* Avatar */}
            <Avatar className="w-8 h-8 flex-shrink-0 border border-border shadow-sm mt-1">
              <AvatarFallback
                className={cn(
                  'text-xs font-medium',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white'
                )}
              >
                {message.role === 'user' ? (
                  <UserIcon className="w-4 h-4" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
              </AvatarFallback>
            </Avatar>

            {/* Message Content */}
            <div
              className={cn(
                'max-w-[85%] min-w-0 space-y-2',
                message.role === 'user' ? 'items-end' : 'items-start'
              )}
            >
              <div
                className={cn(
                  'rounded-2xl px-5 py-3.5 shadow-sm text-sm',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-sm'
                    : 'bg-card border border-border rounded-tl-sm text-foreground ring-1 ring-border/50'
                )}
              >
                {message.role === 'user' ? (
                  <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                ) : (
                  <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Professional Table Styling
                        table: ({ node, ...props }) => (
                          <div className="my-4 w-full overflow-x-auto rounded-lg border border-border shadow-sm">
                            <table className="w-full text-left text-sm" {...props} />
                          </div>
                        ),
                        thead: ({ node, ...props }) => (
                          <thead className="bg-muted/50 text-xs uppercase font-semibold text-muted-foreground tracking-wider" {...props} />
                        ),
                        th: ({ node, ...props }) => (
                          <th className="px-4 py-3 border-b border-border" {...props} />
                        ),
                        td: ({ node, ...props }) => (
                          <td className="px-4 py-3 border-b border-border last:border-0 align-top" {...props} />
                        ),
                        // Lists
                        ul: ({ node, ...props }) => <ul className="my-2 ml-4 list-disc marker:text-muted-foreground" {...props} />,
                        ol: ({ node, ...props }) => <ol className="my-2 ml-4 list-decimal marker:text-muted-foreground" {...props} />,
                        li: ({ node, ...props }) => <li className="pl-1 my-1" {...props} />,
                        // Typography
                        h1: ({ node, ...props }) => <h1 className="text-lg font-bold mt-4 mb-2" {...props} />,
                        h2: ({ node, ...props }) => <h2 className="text-base font-bold mt-4 mb-2" {...props} />,
                        h3: ({ node, ...props }) => <h3 className="text-sm font-bold mt-3 mb-1 uppercase tracking-wide text-primary" {...props} />,
                        p: ({ node, ...props }) => <p className="leading-relaxed my-2 last:mb-0" {...props} />,
                        code: ({ node, className, children, ...props }) => {
                          const match = /language-(\w+)/.exec(className || '');
                          if (!match) {
                            return <code className="px-1.5 py-0.5 rounded-md bg-muted font-mono text-xs" {...props}>{children}</code>;
                          }
                          return <code className={className} {...props}>{children}</code>;
                        },
                        blockquote: ({ node, ...props }) => <blockquote className="border-l-2 border-primary pl-4 italic my-2 text-muted-foreground" {...props} />,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                )}
                {message.isTyping && (
                  <span className="inline-block w-1.5 h-4 bg-primary/50 ml-1 animate-pulse align-middle" />
                )}
              </div>

              {/* Sources - Perplexity Style (Bottom Row) */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-3 h-3 text-primary" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Sources</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {message.sources.map((source, idx) => (
                      <div
                        key={idx}
                        onClick={() => onSourceClick?.(source.name)}
                        className="group flex flex-col justify-between w-[140px] h-[70px] p-2 rounded-lg bg-card border border-border hover:border-primary/50 hover:bg-muted/50 transition-all cursor-pointer shadow-sm"
                      >
                        <p className="text-xs font-medium text-foreground line-clamp-2 leading-tight" title={source.name}>
                          {source.name}
                        </p>
                        <div className="flex items-center justify-between mt-auto w-full">
                          <div className="flex items-center gap-1.5">
                            <div className={`w-1.5 h-1.5 rounded-full ${source.name.endsWith('.pdf') ? 'bg-red-500' : 'bg-blue-500'}`} />
                            <span className="text-[10px] text-muted-foreground capitalize">
                              {source.name.split('.').pop()}
                            </span>
                          </div>
                          {source.relevance !== undefined && (
                            <span className="text-[10px] font-medium text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded">
                              {Math.round(source.relevance)}%
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-background border-t border-border sticky bottom-0 z-20">
        <form
          onSubmit={handleSubmit}
          className="relative rounded-xl border border-border bg-card shadow-sm hover:border-primary/50 focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all overflow-hidden"
        >
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a follow-up or describe requirements..."
            className="w-full min-h-[60px] max-h-[200px] resize-none border-0 focus-visible:ring-0 bg-transparent py-4 pl-4 pr-14 placeholder:text-muted-foreground/50 leading-relaxed"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            disabled={isGenerating}
          />
          <div className="absolute bottom-3 right-3 flex items-center gap-1">
            {isGenerating ? (
              <div className="h-8 w-8 flex items-center justify-center">
                <RefreshCw className="w-4 h-4 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Button
                type="submit"
                size="icon"
                disabled={!input.trim()}
                className={cn(
                  "h-8 w-8 transition-all duration-200",
                  input.trim() ? "bg-primary hover:bg-primary/90 shadow-sm" : "bg-muted text-muted-foreground hover:bg-muted"
                )}
              >
                <Send className="w-4 h-4" />
              </Button>
            )}
          </div>
        </form>
        <p className="text-[10px] text-center text-muted-foreground/60 mt-2 font-medium tracking-wide">
          AI generated responses can make mistakes. Verify important information.
        </p>
      </div>
    </div>
  );
}
