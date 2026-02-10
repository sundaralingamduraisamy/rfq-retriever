import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const BACKEND = import.meta.env.VITE_BACKEND_URL;

interface RFQMarkdownProps {
    content: string;
}

export const RFQMarkdown: React.FC<RFQMarkdownProps> = ({ content }) => {
    const processedText = useMemo(() => {
        let text = content || "";

        // Stage 1: Replace [[IMAGE_ID:n]] in markdown targets
        text = text.replace(/\(\[\[IMAGE_ID:(\d+)\]\]\)/g, `(${BACKEND}/images/$1)`);

        // Stage 2: Replace stand-alone [[IMAGE_ID:n]] tags
        text = text.replace(/\[\[IMAGE_ID:(\d+)\]\]/g, (match, id) => {
            return `\n\n![VISION COMPONENT: ID ${id}](${BACKEND}/images/${id})\n\n`;
        });

        // Stage 3: Filter out unwanted TOC entries and process lines
        const lines = text.split('\n');
        const transformedLines = lines
            .filter(line => {
                const trimmed = line.trim();
                // Remove "14. References & Standards" from table of contents
                if (/^14\.\s+References\s+(&|and)\s+Standards/i.test(trimmed)) {
                    return false;
                }
                return true;
            })
            .map(line => {
                const trimmed = line.trim();

                // SKIP: If already a markdown header, skip
                if (trimmed.startsWith('#')) return line;

                // SKIP: If it's the TOC section specifically
                if (/^1\.\s+TABLE OF CONTENTS/i.test(trimmed)) return line;

                const cleanLine = trimmed.replace(/^\*\*|\*\*$/g, '').trim();

                // Match "1. Title" or "1.1 Title" or "Section 1: Title"
                const isHeaderLike = /^(\d+\.|\d+\.\d+|Section\s+\d+:)/i.test(cleanLine);
                if (isHeaderLike && cleanLine.length < 100) {
                    return `## ${cleanLine}`;
                }
                return line;
            });

        return transformedLines.join('\n');
    }, [content]);

    return (
        <div className="prose prose-slate prose-sm md:prose-base !prose-headings:text-slate-900 !prose-p:text-slate-600 prose-img:rounded-xl prose-img:shadow-lg">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    h2: ({ node, ...props }) => (
                        <h2 className="text-2xl font-extrabold text-[#006680] mt-16 mb-8 border-b-2 pb-3 border-slate-200 uppercase tracking-tight" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                        <h3 className="text-2xl font-bold text-[#006680] mt-10 mb-6 capitalize" {...props} />
                    ),
                    p: ({ node, ...props }) => (
                        <p className="mb-12 leading-[1.8] whitespace-pre-wrap text-slate-800 font-sans text-lg" {...props} />
                    ),
                    strong: ({ node, ...props }) => (
                        <strong className="font-bold text-[#006680]" {...props} />
                    ),
                    table: ({ node, ...props }) => (
                        <div className="my-8 w-full overflow-hidden rounded-xl border border-slate-200 shadow-sm">
                            <table className="w-full text-left text-sm" {...props} />
                        </div>
                    ),
                    thead: ({ node, ...props }) => <thead className="bg-slate-50 text-slate-500 uppercase text-[11px] font-bold tracking-wider" {...props} />,
                    th: ({ node, ...props }) => <th className="px-6 py-4 border-b border-slate-200" {...props} />,
                    td: ({ node, ...props }) => <td className="px-6 py-4 border-b border-slate-100 last:border-0" {...props} />,
                    img: ({ node, ...props }) => (
                        <div className="my-12 flex flex-col items-center">
                            <img
                                {...props}
                                className="max-h-[600px] w-full object-contain rounded-2xl shadow-2xl border border-slate-200"
                                onError={(e) => {
                                    console.error("❌ Image failed to load:", props.src);
                                    e.currentTarget.style.display = 'none';
                                    const fallback = document.createElement('div');
                                    fallback.className = "p-4 border-2 border-dashed border-red-200 rounded-xl bg-red-50 text-red-500 text-xs text-center";
                                    fallback.innerText = `Image Failed to Load (ID: ${props.src?.split('/').pop()})`;
                                    e.currentTarget.parentElement?.appendChild(fallback);
                                }}
                            />
                            <span className="mt-4 text-[11px] uppercase tracking-[0.2em] text-slate-500 font-black bg-slate-100 px-4 py-2 rounded-full border border-slate-200 shadow-sm">
                                {props.alt || "Vision Component Illustration"}
                            </span>
                        </div>
                    )
                }}
            >
                {processedText}
            </ReactMarkdown>
        </div>
    );
};
