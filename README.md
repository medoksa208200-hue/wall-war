# حرب السور — APK

## أسهل طريقة (من غير ما تنزل حاجة): GitHub
1. اعمل ريبو جديد على GitHub وارفع محتوى الفولدر ده كله.
2. ادخل تبويب **Actions** → هتلاقي **Build APK** شغال لوحده (أو دوس Run workflow).
3. بعد ~5 دقايق افتح الـ run → تحت **Artifacts** نزّل `wall-war-apk` → جواه `app-debug.apk`.
4. ابعته للموبايل وسطّبه (اسمح بـ "تثبيت من مصادر غير معروفة").

## من Android Studio
```
npm install
npx cap sync android
npx cap open android
```
وبعدين Build → Build APK(s).

## تعديل اللعبة
اللعبة كلها في `www/index.html`. عدّل فيه وبعدين `npx cap sync android` وابني تاني.
