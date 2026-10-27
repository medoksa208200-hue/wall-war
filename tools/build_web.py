#!/usr/bin/env python3
"""Build the app's web bundle from src/game.html.

  python3 tools/build_web.py [--notes "what changed"] [--min-native N]

- www/game.html   full game document (the APK ships it; phones also download it as an update)
- www/version.json  {v, minNative, apk, notes}  read by every installed app at start-up
- www/index.html  tiny loader: picks the newest game (downloaded or bundled) and runs it

The version number is read from `const VERSION=` in src/game.html — bump it for every release.
NATIVE in the loader is the Android-side version: bump it (and versionCode) only when Java/plugins change.
"""
import json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
NATIVE = 3
REPO_RAW = "https://raw.githubusercontent.com/medoksa208200-hue/wall-war/main/www/"
APK = "https://github.com/medoksa208200-hue/wall-war/releases/download/latest/wall-war.apk"

args = sys.argv[1:]
notes = args[args.index("--notes") + 1] if "--notes" in args else ""
min_native = int(args[args.index("--min-native") + 1]) if "--min-native" in args else NATIVE

src = (ROOT / "src/game.html").read_text(encoding="utf-8")
ver = int(re.search(r"const VERSION=(\d+);", src).group(1))
i = src.index("</style>") + len("</style>")
head = ('<!doctype html><html lang="ar" dir="ltr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">'
        '<meta name="theme-color" content="#120d0a">')
game = head + src[:i] + "</head><body>" + src[i:] + "</body></html>"
(ROOT / "www/game.html").write_text(game, encoding="utf-8")
(ROOT / "www/version.json").write_text(json.dumps({"v": ver, "minNative": min_native, "apk": APK, "notes": notes}, ensure_ascii=False), encoding="utf-8")

loader = """<!doctype html><html lang="ar"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="theme-color" content="#120d0a">
<style>html,body{height:100%;margin:0;background:#120d0a;color:#ffe9c7;font-family:system-ui,sans-serif}
body{display:flex;align-items:center;justify-content:center;flex-direction:column;gap:14px}
b{font-size:34px;color:#f2b53c}i{width:26px;height:26px;border:3px solid #3a2a1e;border-top-color:#f2b53c;border-radius:50%;animation:s 1s linear infinite}
@keyframes s{to{transform:rotate(360deg)}}</style></head>
<body><b>حرب السور</b><i></i>
<script>
/* Auto-update loader: runs the newest game it can get. Online → checks GitHub for a newer game and keeps it;
   offline → runs the last downloaded game (or the one inside the APK). */
(async function(){
  var NATIVE=__NATIVE__, BUNDLED=__VER__, BASE='__BASE__';
  function get(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function put(k,v){try{localStorage.setItem(k,v);return true}catch(e){return false}}
  function tf(u,ms){var c=new AbortController(),t=setTimeout(function(){c.abort()},ms);return fetch(u,{signal:c.signal,cache:'no-store'}).finally(function(){clearTimeout(t)})}
  var html=null,ver=BUNDLED,cv=+get('wg_v')||0,force=get('wg_force')==='1';
  if(force)try{localStorage.removeItem('wg_force')}catch(e){}
  if(cv>BUNDLED){html=get('wg_html');if(html)ver=cv}
  var info=null;
  try{info=await (await tf(BASE+'version.json?t='+Date.now(),force?6000:2500)).json();put('wg_info',JSON.stringify(info))}catch(e){try{info=JSON.parse(get('wg_info'))}catch(_){}}
  if(info&&info.v>ver&&(info.minNative||0)<=NATIVE){
    try{var h=await (await tf(BASE+'game.html?v='+info.v,8000)).text();
      if(h.indexOf('WALLWAR_GAME')>0){html=h;ver=info.v;put('wg_html',h);put('wg_v',String(info.v))}}catch(e){}
  }
  if(!html){html=await (await fetch('game.html')).text();ver=BUNDLED}
  window.WALL={native:NATIVE,ver:ver,apkNeeded:!!(info&&(info.minNative||0)>NATIVE),apk:info&&info.apk,notes:info&&info.notes};
  document.open();document.write(html);document.close();
})();
</script></body></html>"""
loader = loader.replace("__NATIVE__", str(NATIVE)).replace("__VER__", str(ver)).replace("__BASE__", REPO_RAW)
(ROOT / "www/index.html").write_text(loader, encoding="utf-8")
print(f"built game v{ver} (native {NATIVE}, minNative {min_native}) — {len(game)//1024} KB")
