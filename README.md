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
mkdir -p /tmp/wallwar-sprites && cp art/enemy-sheet.png /tmp/wallwar-sprites/enemy.png && cp art/player-sheet-marked.png /tmp/wallwar-sprites/player.png
python3 tools/sprites_cut.py /tmp/wallwar-sprites/enemy.png /tmp/wallwar-sprites
python3 tools/sprites_cut.py /tmp/wallwar-sprites/player.png /tmp/wallwar-sprites
cp /tmp/wallwar-sprites/player_keyed.png /tmp/wallwar-sprites/player_marked.png
python3 tools/sprites_parts.py /tmp/wallwar-sprites   # الخوذة ماجنتا، الجزمة سيان، السلاح أصفر ← طبقات للاسكنات
SPR_DIR=/tmp/wallwar-sprites python3 tools/sprites_pack.py   # يطلع sprites.js — حطه مكان سطر SPRITES في src/game.html
```
كل شيت لازم يكون صفين × ٨ وضعيات بنفس الترتيب اللي في البرومت، على خلفية خضرا صافية.
شيت المشي (`art/player-walk-marked.png`، ٤ صفوف × ٦): يتقطّع بنفس الطريقة (4 صفوف) وبعدين `python3 tools/sprites_walk_pack.py <dir>` يطلع walk.js — حطه مكان سطر WALKSHEET في src/game.html.
شيت اللاعب لازم الخوذة فيه ماجنتا والجزمة سيان والسلاح أصفر (علشان الاسكنات).

## البناء
الـ APK بيتبني تلقائي على GitHub Actions مع كل push، وبيتنشر في Release اسمه `latest`.
