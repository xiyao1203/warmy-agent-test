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
                  var p=localStorage.getItem('theme');
                  if(p!=='dark'&&p!=='light'&&p!=='system') p='system';
                  var m=window.matchMedia('(prefers-color-scheme: dark)');
                  var apply=function(){
                    var current=localStorage.getItem('theme');
                    if(current!=='dark'&&current!=='light'&&current!=='system') current='system';
                    var t=current==='system'?(m.matches?'dark':'light'):current;
                    var r=document.documentElement;
                    r.classList.remove('dark','light');
                    r.classList.add(t);
                    r.dataset.theme=t;
                    r.dataset.themePreference=current;
                    r.style.colorScheme=t;
                  };
                  apply();
                  m.addEventListener('change',function(){
                    var current=localStorage.getItem('theme');
                    if(current===null||current==='system') apply();
                  });
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
