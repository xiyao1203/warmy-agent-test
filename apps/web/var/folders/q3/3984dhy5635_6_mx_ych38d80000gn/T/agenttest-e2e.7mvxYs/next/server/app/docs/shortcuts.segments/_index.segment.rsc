1:"$Sreact.fragment"
3:I[11568,["/_next/static/chunks/2asf0xwdfpqy4.js"],"QueryProvider"]
4:I[42145,["/_next/static/chunks/3r9-td-yrt42d.js","/_next/static/chunks/1g2trrj6to2c8.js"],"default"]
5:I[44979,["/_next/static/chunks/3r9-td-yrt42d.js","/_next/static/chunks/1g2trrj6to2c8.js"],"default"]
:HL["/_next/static/chunks/0a8uz1mt-3632.css","style"]
2:T473,
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
            0:{"rsc":["$","$1","c",{"children":[[["$","link","0",{"rel":"stylesheet","href":"/_next/static/chunks/0a8uz1mt-3632.css","precedence":"next"}],["$","script","script-0",{"src":"/_next/static/chunks/2asf0xwdfpqy4.js","async":true}]],["$","html",null,{"lang":"zh-CN","suppressHydrationWarning":true,"children":[["$","head",null,{"children":["$","script",null,{"dangerouslySetInnerHTML":{"__html":"$2"}}]}],["$","body",null,{"children":["$","$L3",null,{"children":["$","$L4",null,{"parallelRouterKey":"children","template":["$","$L5",null,{}],"notFound":[[["$","title",null,{"children":"404: This page could not be found."}],["$","div",null,{"style":{"fontFamily":"system-ui,\"Segoe UI\",Roboto,Helvetica,Arial,sans-serif,\"Apple Color Emoji\",\"Segoe UI Emoji\"","height":"100vh","textAlign":"center","display":"flex","flexDirection":"column","alignItems":"center","justifyContent":"center"},"children":["$","div",null,{"children":[["$","style",null,{"dangerouslySetInnerHTML":{"__html":"body{color:#000;background:#fff;margin:0}.next-error-h1{border-right:1px solid rgba(0,0,0,.3)}@media (prefers-color-scheme:dark){body{color:#fff;background:#000}.next-error-h1{border-right:1px solid rgba(255,255,255,.3)}}"}}],["$","h1",null,{"className":"next-error-h1","style":{"display":"inline-block","margin":"0 20px 0 0","padding":"0 23px 0 0","fontSize":24,"fontWeight":500,"verticalAlign":"top","lineHeight":"49px"},"children":404}],["$","div",null,{"style":{"display":"inline-block"},"children":["$","h2",null,{"style":{"fontSize":14,"fontWeight":400,"lineHeight":"49px","margin":0},"children":"This page could not be found."}]}]]}]}]],[]]}]}]}]]}]]}],"isPartial":false,"staleTime":300,"varyParams":null,"buildId":"QOmGEJPch0wlleG9JDq7I"}
