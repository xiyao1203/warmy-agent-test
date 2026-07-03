"use client";

import type { ComponentPropsWithoutRef, MouseEvent } from "react";
import { useCallback, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import { Check, Copy, Play, Sparkles } from "lucide-react";

type MarkdownContentProps = {
  content: string;
  isStreaming?: boolean;
};

export function MarkdownContent({
  content,
  isStreaming = false,
}: MarkdownContentProps) {
  return (
    <div
      className="prose prose-sm dark:prose-invert max-w-none overflow-hidden break-words [&_pre]:max-w-full [&_pre]:overflow-x-auto [&_pre]:rounded-[var(--radius-md)] [&_pre]:bg-[var(--canvas-soft)] [&_pre]:p-3 [&_code]:text-[0.85em] [&_code:not(pre_code)]:rounded [&_code:not(pre_code)]:bg-[var(--canvas-soft)] [&_code:not(pre_code)]:px-1 [&_code:not(pre_code)]:py-0.5 [&_p]:leading-7 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-0.5 [&_blockquote]:border-l-2 [&_blockquote]:border-[var(--primary)] [&_blockquote]:pl-3 [&_blockquote]:italic [&_blockquote]:text-[var(--muted)] [&_table]:block [&_table]:max-w-full [&_table]:overflow-x-auto [&_table]:border-collapse [&_th]:whitespace-nowrap [&_th]:border [&_th]:border-[var(--hairline)] [&_th]:px-3 [&_th]:py-1.5 [&_th]:text-left [&_td]:border [&_td]:border-[var(--hairline)] [&_td]:px-3 [&_td]:py-1.5 [&_a]:text-[var(--primary)] [&_a]:underline"
      data-testid="markdown-content"
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          code: CodeBlock,
        }}
      >
        {content}
      </ReactMarkdown>
      {isStreaming ? (
        <span className="ml-0.5 inline-block h-[1.05em] w-0.5 animate-pulse rounded-full bg-[var(--ink)] align-text-bottom" />
      ) : null}
    </div>
  );
}

function CodeBlock({
  className,
  children,
  ...props
}: ComponentPropsWithoutRef<"code">) {
  const match = /language-(\w+)/.exec(className || "");
  const isInline = !match;

  if (isInline) {
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  }

  return (
    <CodeBlockWithCopy className={className} language={match[1]} {...props}>
      {children}
    </CodeBlockWithCopy>
  );
}

function CodeBlockWithCopy({
  children,
  className,
  language,
  ...props
}: ComponentPropsWithoutRef<"code"> & { language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(
    (e: MouseEvent) => {
      e.stopPropagation();
      const text = String(children).replace(/\n$/, "");
      void navigator.clipboard.writeText(text).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      });
    },
    [children],
  );

  const dispatchCodeAction = useCallback(
    (action: "run" | "explain") => {
      const codeText = String(children).replace(/\n$/, "");
      window.dispatchEvent(
        new CustomEvent("code-action", {
          detail: { action, code: codeText, language },
        }),
      );
    },
    [children, language],
  );

  return (
    <div className="group relative my-2">
      <div className="flex items-center justify-between rounded-t-[var(--radius-md)] bg-[var(--canvas)] px-3 py-1 border-b border-[var(--hairline)]">
        <span className="text-[0.65rem] font-mono font-medium uppercase text-[var(--muted)]">
          {language}
        </span>
        <div className="flex items-center gap-0.5 opacity-0 transition-all group-hover:opacity-100">
          <button
            aria-label="复制代码"
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[0.65rem] text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
            onClick={handleCopy}
            type="button"
          >
            {copied ? (
              <>
                <Check className="size-3 text-[var(--success)]" />
                <span className="hidden sm:inline">已复制</span>
              </>
            ) : (
              <>
                <Copy className="size-3" />
                <span className="hidden sm:inline">复制</span>
              </>
            )}
          </button>
          <button
            aria-label="运行代码"
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[0.65rem] text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
            onClick={() => dispatchCodeAction("run")}
            type="button"
          >
            <Play className="size-3" />
            <span className="hidden sm:inline">运行</span>
          </button>
          <button
            aria-label="解释代码"
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[0.65rem] text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
            onClick={() => dispatchCodeAction("explain")}
            type="button"
          >
            <Sparkles className="size-3" />
            <span className="hidden sm:inline">解释</span>
          </button>
        </div>
      </div>
      <code className={`${className} block rounded-t-none`} {...props}>
        {children}
      </code>
    </div>
  );
}
