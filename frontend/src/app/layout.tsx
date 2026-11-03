import type { Metadata } from "next";
import "./globals.css";
import React from "react";
import { NuqsAdapter } from "nuqs/adapters/next/app";

export const metadata: Metadata = {
  title: "W.AgentChat",
  description: "W.AgentChat — Wistron agent chat UI",
};

/** Avoid theme flash before hydration; mirrors readStoredUiTheme migration. */
const themeInitScript = `
(function(){
  try {
    var k='ai_prepare.ui_theme';
    var t=localStorage.getItem(k);
    if(!t){
      var o=localStorage.getItem('ai_prepare.ocean');
      if(o){ try{ var p=JSON.parse(o); t=p&&p.theme; }catch(e){} }
    }
    if(t==='dark') t='wistron-dark';
    else if(t==='light') t='wistron-light';
    else if(t==='wistron' || t==='wistron-classic') t='wistron-dark';
    if(t!=='wistron-dark'&&t!=='wistron-light') t='wistron-dark';
    document.documentElement.setAttribute('data-theme', t);
  } catch(e) {
    document.documentElement.setAttribute('data-theme','wistron-dark');
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-theme="wistron-dark"
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      {/* [ai_prepare 修改] 系統字型；主題色由 data-theme + globals.css tokens */}
      <body className="bg-background text-foreground font-sans antialiased">
        <NuqsAdapter>{children}</NuqsAdapter>
      </body>
    </html>
  );
}
