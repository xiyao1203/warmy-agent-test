"use client";

import { useState } from "react";
import { Search, X } from "lucide-react";
import Link from "next/link";

export interface HelpTopic {
  id: string;
  title: string;
  description: string;
  href: string;
  category: string;
}

interface HelpSearchProps {
  topics: HelpTopic[];
}

export function HelpSearch({ topics }: HelpSearchProps) {
  const [query, setQuery] = useState("");
  const normalizedQuery = query.trim().toLocaleLowerCase();

  const filteredTopics = normalizedQuery
    ? topics.filter(
        (topic) =>
          topic.title.toLocaleLowerCase().includes(normalizedQuery) ||
          topic.description.toLocaleLowerCase().includes(normalizedQuery) ||
          topic.category.toLocaleLowerCase().includes(normalizedQuery),
      )
    : topics;

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]" />
        <input
          className="h-10 w-full rounded-lg border border-[var(--hairline)] bg-[var(--surface)] pl-10 pr-10 text-sm outline-none placeholder:text-[var(--body)] focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索帮助文档..."
          type="search"
          value={query}
        />
        {query && (
          <button
            aria-label="清空搜索"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)] hover:text-[var(--ink)]"
            onClick={() => setQuery("")}
          >
            <X className="size-4" />
          </button>
        )}
      </div>

      {normalizedQuery && (
        <p aria-live="polite" className="text-xs text-[var(--muted)]">
          找到 {filteredTopics.length} 条结果
        </p>
      )}

      {filteredTopics.length === 0 ? (
        <div className="rounded-lg border border-[var(--hairline)] bg-[var(--card)] p-8 text-center">
          <Search className="mx-auto size-8 text-[var(--muted)]" />
          <p className="mt-3 text-sm text-[var(--muted)]">没有找到相关内容</p>
          <div className="mt-3 flex items-center justify-center gap-3 text-sm">
            <button
              className="text-[var(--primary)] hover:underline"
              onClick={() => setQuery("")}
            >
              清空搜索
            </button>
            <span aria-hidden="true" className="text-[var(--hairline-strong)]">
              ·
            </span>
            <Link
              className="text-[var(--primary)] hover:underline"
              href="/feedback"
            >
              提交反馈
            </Link>
          </div>
        </div>
      ) : (
        <div
          aria-label="搜索结果"
          className="grid gap-3 sm:grid-cols-2"
          role="region"
        >
          {filteredTopics.map((topic) => (
            <Link
              key={topic.id}
              className="rounded-lg border border-[var(--hairline)] bg-[var(--card)] p-4 transition-colors hover:border-[var(--primary)] hover:bg-[var(--primary-subtle)]"
              href={topic.href}
            >
              <span className="mb-1 inline-block rounded bg-[var(--muted)] px-2 py-0.5 text-xs text-[var(--muted)]">
                {topic.category}
              </span>
              <h3 className="font-medium">{topic.title}</h3>
              <p className="mt-1 text-sm text-[var(--muted)]">
                {topic.description}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
