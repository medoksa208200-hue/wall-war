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
NATIVE = 5
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
/* Loader: starts instantly with the newest COMPLETE game it has (IndexedDB, then localStorage, then the one inside the APK).
   The real version is read from inside each copy, so a half-saved update can never be mistaken for a new one.
   The game itself downloads updates in the background and offers a restart. */
(async function(){
  var NATIVE=__NATIVE__, BUNDLED=__VER__;
  function verOf(h){if(!h||h.indexOf('WALLWAR_GAME')<0)return 0;var m=/const VERSION=(\\d+);/.exec(h);return m?+m[1]:0}
  function idbGet(){return new Promise(function(res){try{var rq=indexedDB.open('wallwar',1);rq.onupgradeneeded=function(){rq.result.createObjectStore('kv')};
    rq.onsuccess=function(){try{var g=rq.result.transaction('kv').objectStore('kv').get('game');g.onsuccess=function(){res(g.result||null)};g.onerror=function(){res(null)}}catch(e){res(null)}};rq.onerror=function(){res(null)}}catch(e){res(null)}});}
  var best=null,bv=0;
  var rec=await Promise.race([idbGet(),new Promise(function(r){setTimeout(function(){r(null)},1500)})]);
  if(rec&&rec.html){var v=verOf(rec.html);if(v>bv){bv=v;best=rec.html}}
  try{var ls=localStorage.getItem('wg_html'),lv=verOf(ls);if(lv>bv){bv=lv;best=ls}}catch(e){}
  if(bv<=BUNDLED){best=await (await fetch('game.html')).text();bv=BUNDLED}
  window.WALL={native:NATIVE,ver:bv,apkNeeded:false};
  document.open();document.write(best);document.close();
})();
</script></body></html>"""
loader = loader.replace("__NATIVE__", str(NATIVE)).replace("__VER__", str(ver)).replace("__BASE__", REPO_RAW)
(ROOT / "www/index.html").write_text(loader, encoding="utf-8")
print(f"built game v{ver} (native {NATIVE}, minNative {min_native}) — {len(game)//1024} KB")
