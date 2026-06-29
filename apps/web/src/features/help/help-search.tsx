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

  const filteredTopics = query
    ? topics.filter(
        (topic) =>
          topic.title.toLowerCase().includes(query.toLowerCase()) ||
          topic.description.toLowerCase().includes(query.toLowerCase()) ||
          topic.category.toLowerCase().includes(query.toLowerCase())
      )
    : topics;

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--text-muted)]" />
        <input
          className="h-10 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] pl-10 pr-10 text-sm outline-none placeholder:text-[var(--text-subtle)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索帮助文档..."
          type="search"
          value={query}
        />
        {query && (
          <button
            aria-label="清空搜索"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text)]"
            onClick={() => setQuery("")}
          >
            <X className="size-4" />
          </button>
        )}
      </div>

      {filteredTopics.length === 0 ? (
        <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-8 text-center">
          <Search className="mx-auto size-8 text-[var(--text-muted)]" />
          <p className="mt-3 text-sm text-[var(--text-muted)]">
            没有找到相关内容
          </p>
          <button
            className="mt-2 text-sm text-[var(--primary)] hover:underline"
            onClick={() => setQuery("")}
          >
            清空搜索
          </button>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {filteredTopics.map((topic) => (
            <Link
              key={topic.id}
              className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 transition-colors hover:border-[var(--accent)] hover:bg-[var(--accent-subtle)]"
              href={topic.href}
            >
              <span className="mb-1 inline-block rounded bg-[var(--muted)] px-2 py-0.5 text-xs text-[var(--text-muted)]">
                {topic.category}
              </span>
              <h3 className="font-medium">{topic.title}</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                {topic.description}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
