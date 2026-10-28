# حرب السور

لعبة 2D لاتنين ورا سورين: استخبى، اتحرك، وطّي أو نام، وفي دورك نشّن واضرب أو ارمي قنبلة.
١٠ مودات، ٤ مستويات صعوبة، اسكنات، ولعب بالبلوتوث من غير نت.

## تنزيل التطبيق
https://github.com/medoksa208200-hue/wall-war/releases/download/latest/wall-war.apk

## التحديث التلقائي
التطبيق بيفتح `www/index.html` (لودر صغير). اللودر بيقرا `www/version.json` من GitHub:
لو فيه نسخة أحدث بينزّل `www/game.html` ويشغّلها ويحفظها علشان تشتغل من غير نت.

**علشان تنزّل تحديث للعبة لكل الأجهزة:**
1. عدّل في `src/game.html` وزوّد `const VERSION=`.
2. `python3 tools/build_web.py --notes "اللي اتغير"`
3. اعمل commit و push على `main`. الأجهزة هتاخد التحديث أول ما اللعبة تتفتح على نت (خلال ~٥ دقايق من الـ push).

**لو غيرت كود أندرويد (Java / plugins):** زوّد `NATIVE` في `tools/build_web.py` و `versionCode` في `android/app/build.gradle`،
وابني بـ `--min-native <الرقم الجديد>`. الأجهزة القديمة هيظهرلها زرار تنزّل الـ APK الجديد.

## الكراكترات
الصور الأصلية في `art/`. لتقطيعها من جديد:
```
mkdir -p /tmp/wallwar-sprites && cp art/enemy-sheet.png /tmp/wallwar-sprites/enemy.png && cp art/player-sheet.png /tmp/wallwar-sprites/player.png
python3 tools/sprites_cut.py /tmp/wallwar-sprites/enemy.png /tmp/wallwar-sprites
python3 tools/sprites_cut.py /tmp/wallwar-sprites/player.png /tmp/wallwar-sprites
python3 tools/sprites_parts.py /tmp/wallwar-sprites   # يفصل الخوذة والجزمة والسلاح للاسكنات
SPR_DIR=/tmp/wallwar-sprites python3 tools/sprites_pack.py   # يطلع sprites.js — حطه مكان سطر SPRITES في src/game.html
```
كل شيت لازم يكون صفين × ٨ وضعيات بنفس الترتيب اللي في البرومت، على خلفية خضرا صافية.

## البناء
الـ APK بيتبني تلقائي على GitHub Actions مع كل push، وبيتنشر في Release اسمه `latest`.
