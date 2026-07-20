import type { Metadata } from "next";
import type { ReactNode } from "react";

import { QueryProvider } from "@/lib/query/provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Warmy Agent Test",
  description: "Agent automation testing and security evaluation platform",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function(){
                try {
                  var stored=localStorage.getItem('theme');
                  var theme=stored==='dark'||stored==='light'
                    ? stored
                    : (window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
                  if(stored!==theme) localStorage.setItem('theme',theme);
                  var root=document.documentElement;
                  root.classList.remove('dark','light');
                  root.classList.add(theme);
                  root.dataset.theme=theme;
                  root.dataset.themePreference=theme;
                  root.style.colorScheme=theme;
                } catch(e){}
              })();
            `,
          }}
        />
      </head>
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
