# claude-reel-editor 🎬

**[العربية](#بالعربية) · [English](#english)**

A Claude Code skill that turns a raw talking-head recording into a publish-ready reel — silence removal, jump cuts, punch-in reframes, word-timed captions, full-screen motion-graphic interludes, audio leveling, preview, render. The edit is built as code with [HyperFrames](https://github.com/heygen-com/hyperframes), so every caption and cut stays editable.

---

## بالعربية

مهارة لـ Claude Code تحوّل فيديو خام (شخص يتكلم أمام الكاميرا) إلى ريل جاهز للنشر:
شيل الصمت، القطعات، الزوم على الوجه في اللحظات المهمة، كابشنز متزامنة مع كل كلمة، مشاهد موشن جرافيكس بملء الشاشة، ضبط الصوت، معاينة، ثم تصدير.

المونتاج يُبنى **بالكود** عبر HyperFrames (مفتوحة المصدر من HeyGen)، يعني تقدر تقول لـ Claude «غيّر الكلمة دي» أو «اقصر المشهد التالت» بدل ما يعيد توليد الفيديو كله.

### التثبيت

```bash
# 1) المتطلبات: Node.js 22+ و FFmpeg و Python
brew install ffmpeg            # macOS  (Windows: winget install ffmpeg)

# 2) مهارات HyperFrames (المحرّك)
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes

# 3) هذه المهارة
claude plugin marketplace add Mereyani/claude-reel-editor
claude plugin install reel-editor@claude-reel-editor
```

أو بدون نظام الإضافات: `npx skills add Mereyani/claude-reel-editor`

### الجديد في 0.2.0

- **أوامر المونتاج بالصوت:** قل أثناء التصوير «اقطع هذه اللقطة» أو «أريد زوم على وجهي» أو «اعرض موقعي هنا» وسينفّذها.
- **قص أدق:** يجمع بين توقيت الكلمات وكشف الصمت الحقيقي، فلا يُقص كلام ولا يبقى صمت.
- **فيديوهات الجوال وواتساب:** يحوّلها لمعدل إطارات ثابت ويضبط مستوى الصوت (−14 LUFS) قبل المونتاج.
- **مُجرَّبة فعليًا:** فيديو عربي 72 ثانية → ريل 49 ثانية مع مشاهد جرافيك وتقسيم شاشة وزوم، تصدير في أقل من دقيقتين.

### الاستخدام

1. أنشئ مجلدًا جديدًا وضع فيه الفيديو الخام (واختياريًا: `fonts/` ، `logos/` ، `brand.md`).
2. افتح Claude Code على هذا المجلد واكتب مثلًا:
   > منتج الفيديو ده ريل لإنستغرام

   أو للنسخة السريعة الأخف:
   > اعمل مونتاج سريع: شيل الصمت وحط كابشنز بس
3. Claude سيفحص المتطلبات، يفرّغ الكلام، يخطط القطعات، يبني المشروع، ثم **يتوقف ويعطيك رابط معاينة**. وافق أو اطلب تعديلات، وبعدها يصدّر `final.mp4`.

### هل يستحق؟ (تقييم صريح)

| ✅ نقاط القوة | ⚠️ الحدود |
|---|---|
| ممتاز لمحتوى «شخص يتكلم» القصير (ريلز، شورتس، تيك توك) | ريل 30 ثانية بالوضع الكامل يأخذ تقريبًا 20–40 دقيقة ويستهلك جزءًا ملحوظًا من حدّ الاستخدام |
| كل شيء قابل للتعديل لاحقًا لأنه كود | ضعيف مع المونتاج السينمائي أو متعدد الكاميرات أو المعتمد على لقطات خارجية كثيرة |
| لا تكلفة إضافية فوق اشتراك Claude | التفريغ الصوتي للهجات يحتاج مراجعة (المهارة تُلزم Claude بتصحيحه) |
| دعم قوي للعربية (اتجاه RTL، خطوط، كابشنز) | يحتاج تثبيت أدوات (Node و FFmpeg و Python) أول مرة |

**الخلاصة:** استخدم الوضع `quick` للنشر اليومي، والوضع الكامل للفيديوهات المهمة. وراجع دائمًا قبل النشر.

### الفكرة والمصدر

الفكرة مستوحاة من فيديو [«Claude Opus 5.5 منتج الفيديو ده بالكامل من برومت واحد»](https://www.youtube.com/watch?v=CJT-5n5qffQ) لقناة **مدرسة الذكاء الاصطناعي** ([صفحة الموارد](https://arabianaischool.com/claude-reel-editing/)).
الفرق: الفيديو يستخدم برومت طويل لمرة واحدة بأسلوب ثابت؛ هذا المشروع يحوّله إلى **مهارة قابلة لإعادة الاستخدام** بأوضاع وأساليب قابلة للتبديل، مع فحص مسبق وسكربت يحسب نقاط القص بدقة الإطار.

---

## English

### Install

```bash
# prerequisites: Node.js 22+, FFmpeg, Python
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes

claude plugin marketplace add Mereyani/claude-reel-editor
claude plugin install reel-editor@claude-reel-editor
```

Or standalone: `npx skills add Mereyani/claude-reel-editor`

### Use

Put the raw video in an empty folder (optionally `fonts/`, `logos/`, `brand.md`), open Claude Code there, and ask: *"edit this into an Instagram reel"* — or *"quick edit: just cut the silences and add captions"*. Claude runs preflight, transcribes, plans cuts, builds the HyperFrames project, then **stops with a preview link** for your approval before rendering `final.mp4`.

### What's inside

```
skills/reel-editor/
├── SKILL.md                          # the workflow (preflight → intake → analyze → cut → storyboard → build → verify → render)
├── references/
│   ├── editing-rules.md              # cuts, crop states, beat types, captions, motion, audio, safe zones
│   ├── style-editorial-paper.md      # default visual preset (copy it to make your own)
│   ├── rtl-and-fonts.md              # Arabic/RTL shaping, font discovery, dialect transcripts
│   ├── spoken-cues.md                # "cut this", "zoom on my face", "show my site here" said while recording
│   └── hyperframes-notes.md          # setup fixes, lint codes that matter, fonts, commands
└── scripts/
    ├── preflight.sh                  # checks node 22+, ffmpeg, python, faster-whisper, HyperFrames, Chrome
    └── plan_cuts.py                  # word timestamps (+ ffmpeg silences) → frame-accurate cuts, captions.srt,
                                      # and a baked CFR, loudness-normalised A-roll (--bake)
```

`plan_cuts.py` is stdlib-only; run `python3 skills/reel-editor/scripts/plan_cuts.py --selftest`.

### Honest expectations

Good for short talking-head content. A 30 s reel in full mode takes roughly 20–40 min of agent time; `quick` mode is much lighter. Not a replacement for an editor on cinematic, multi-cam or b-roll-heavy work. Always review before posting.

### Credits

Inspired by [this video](https://www.youtube.com/watch?v=CJT-5n5qffQ) by **Arabian AI School** (مدرسة الذكاء الاصطناعي). Rendering engine and core skills: [HyperFrames](https://github.com/heygen-com/hyperframes) by HeyGen (Apache 2.0). This repo is an independent project, not affiliated with either.

MIT License.
