module.exports=[9551,a=>{"use strict";a.s(["QueryProvider",()=>b]);let b=(0,a.i(38233).registerClientReference)(function(){throw Error("Attempted to call QueryProvider() from the server but QueryProvider is on the client. It's not possible to invoke a client function from the server, it can only be rendered as a Component or passed to props of a Client Component.")},"[project]/apps/web/src/lib/query/provider.tsx <module evaluation>","QueryProvider")},87123,a=>{"use strict";a.s(["QueryProvider",()=>b]);let b=(0,a.i(38233).registerClientReference)(function(){throw Error("Attempted to call QueryProvider() from the server but QueryProvider is on the client. It's not possible to invoke a client function from the server, it can only be rendered as a Component or passed to props of a Client Component.")},"[project]/apps/web/src/lib/query/provider.tsx","QueryProvider")},28840,a=>{"use strict";a.i(9551);var b=a.i(87123);a.n(b)},77930,a=>{"use strict";var b=a.i(6855),c=a.i(28840);a.s(["default",0,function({children:a}){return(0,b.jsxs)("html",{lang:"zh-CN",suppressHydrationWarning:!0,children:[(0,b.jsx)("head",{children:(0,b.jsx)("script",{dangerouslySetInnerHTML:{__html:`
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
            `}})}),(0,b.jsx)("body",{children:(0,b.jsx)(c.QueryProvider,{children:a})})]})},"metadata",0,{title:"Warmy Agent Test",description:"Agent automation testing and security evaluation platform"}])},34005,a=>{a.n(a.i(77930))}];

//# sourceMappingURL=apps_web_src_125qyu9._.js.map