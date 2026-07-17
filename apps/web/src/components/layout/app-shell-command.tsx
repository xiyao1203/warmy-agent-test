"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { ChevronRight, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import type { NavigationItem } from "./app-shell-navigation";

export function CommandPalette({
  items,
  onOpenChange,
  open,
}: {
  items: NavigationItem[];
  onOpenChange: (open: boolean) => void;
  open: boolean;
}) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const filtered = items.filter((item) =>
    item.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()),
  );

  function openActiveItem() {
    const item = filtered[activeIndex];
    if (!item) return;
    router.push(item.href);
    onOpenChange(false);
    setQuery("");
    setActiveIndex(0);
  }

  return (
    <DialogPrimitive.Root
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) {
          setQuery("");
          setActiveIndex(0);
        }
      }}
      open={open}
    >
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="app-overlay" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className="app-command-palette"
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            inputRef.current?.focus();
          }}
        >
          <DialogPrimitive.Title className="sr-only">
            全局搜索
          </DialogPrimitive.Title>
          <div className="flex items-center gap-2 border-b border-[var(--hairline)] px-4">
            <Search aria-hidden="true" className="size-4 text-[var(--muted)]" />
            <input
              aria-activedescendant={
                filtered.length ? `command-option-${activeIndex}` : undefined
              }
              aria-controls="command-results"
              aria-label="全局搜索"
              aria-autocomplete="list"
              autoFocus
              className="h-12 min-w-0 flex-1 bg-transparent text-sm text-[var(--ink)] placeholder:text-[var(--muted)]"
              onChange={(event) => {
                setQuery(event.target.value);
                setActiveIndex(0);
              }}
              onKeyDown={(event) => {
                if (!filtered.length) return;
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setActiveIndex((index) => (index + 1) % filtered.length);
                } else if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setActiveIndex(
                    (index) => (index - 1 + filtered.length) % filtered.length,
                  );
                } else if (event.key === "Home") {
                  event.preventDefault();
                  setActiveIndex(0);
                } else if (event.key === "End") {
                  event.preventDefault();
                  setActiveIndex(filtered.length - 1);
                } else if (event.key === "Enter") {
                  event.preventDefault();
                  openActiveItem();
                }
              }}
              placeholder="搜索平台页面…"
              ref={inputRef}
              role="searchbox"
              value={query}
            />
            <kbd>ESC</kbd>
          </div>
          <div className="max-h-[min(26rem,60vh)] overflow-y-auto p-2">
            {filtered.length ? (
              <div aria-label="搜索结果" id="command-results" role="listbox">
                {filtered.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      aria-label={item.label}
                      aria-selected={index === activeIndex}
                      className="app-command-item"
                      data-active={index === activeIndex}
                      href={item.href}
                      id={`command-option-${index}`}
                      key={item.href}
                      onClick={() => {
                        onOpenChange(false);
                        setQuery("");
                        setActiveIndex(0);
                      }}
                      onMouseMove={() => setActiveIndex(index)}
                      role="option"
                    >
                      <Icon aria-hidden="true" className="size-4" />
                      <span>{item.label}</span>
                      <ChevronRight
                        aria-hidden="true"
                        className="ml-auto size-4 text-[var(--muted-soft)]"
                      />
                    </Link>
                  );
                })}
              </div>
            ) : (
              <div className="grid min-h-24 place-items-center text-sm text-[var(--muted)]">
                没有匹配的页面
              </div>
            )}
          </div>
          <div className="flex items-center justify-between border-t border-[var(--hairline)] px-4 py-2 text-xs text-[var(--muted)]">
            <span>快速前往平台任意核心模块</span>
            <span>回车打开</span>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
