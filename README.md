# claude-reel-editor 🎬

**[العربية](#بالعربية) · [English](#english)**

A Claude Code skill that turns a raw talking-head recording into a publish-ready vertical reel (9:16) — silence removal, jump cuts, punch-in reframes, word-timed captions, full-screen motion-graphic interludes, sound effects, voice cleanup, preview, render. The edit is built as code with [HyperFrames](https://github.com/heygen-com/hyperframes), so every caption and cut stays editable.

---

## بالعربية

مهارة لـ Claude Code تحوّل فيديو خام (شخص يتكلم أمام الكاميرا) إلى ريل جاهز للنشر:
شيل الصمت، القطعات، الزوم على الوجه في اللحظات المهمة، كابشنز متزامنة مع كل كلمة، مشاهد موشن جرافيكس بملء الشاشة، ضبط الصوت، معاينة، ثم تصدير.

المونتاج يُبنى **بالكود** عبر HyperFrames (مفتوحة المصدر من HeyGen)، يعني تقدر تقول لـ Claude «غيّر الكلمة دي» أو «اقصر المشهد التالت» بدل ما يعيد توليد الفيديو كله.

### التثبيت

```bash
# 1) المتطلبات: Node.js 22+ و FFmpeg و Python + faster-whisper (يُنزّل نموذج ~3 GB أول مرة)
brew install ffmpeg            # macOS  (Windows: winget install ffmpeg)
python3 -m venv ~/.venvs/reel && ~/.venvs/reel/bin/pip install faster-whisper
# اختياري للوضع المجاني: Ollama  →  https://ollama.com

# 2) مهارات HyperFrames (المحرّك)
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes

# 3) هذه المهارة
claude plugin marketplace add Mereyani/claude-reel-editor
claude plugin install reel-editor@claude-reel-editor
```

أو بدون نظام الإضافات: `npx skills add Mereyani/claude-reel-editor`

### الأوضاع (0.6.0)

| الوضع | ماذا يفعل | من يكتب الكود | التكلفة |
|---|---|---|---|
| `quick` | قص الصمت + كابشن + زوم | **مولّد ثابت** (`build_reel.py`) | رخيص جدًا — أو **مجاني محليًا** مع Ollama |
| `full` | + مشاهد موشن جرافيك، تقسيم شاشة، أوامر صوتية | Claude | الأعلى |
| `faceless` | صوتك فقط + جرافيك متواصل | Claude | عالية |
| مرجع | «مونتج مثل هذا الريل» — يقيس الأسلوب ويعيد بناءه | Claude | عالية |

وفي كل الأوضاع: تنقية الصوت (`--clean`)، مؤثرات صوتية بمستويات مقاسة، قص بدقة الإطار، وتحويل فيديوهات الجوال/واتساب لمعدل إطارات ثابت.

### الوضع المجاني محليًا (Ollama)

التفريغ والقص والتنقية والتوليد والتصدير **كلها محلية أصلًا**. في الوضع `quick` يحتاج القرار فقط: أي الكلمات تُميَّز، وتصحيحات الأسماء. `scripts/local_assist.py` يأخذها من نموذج Ollama محلي ويتحقق منها (يرفض أي كلمة غير موجودة في الكلام، والتصحيحات **مقترحة فقط** لا تُطبَّق تلقائيًا).
الوضع الكامل يحتاج نموذجًا قويًا (يكتب ويصحح مئات الأسطر ويراجع الصور) — النماذج المحلية الصغيرة لا تكفي له.

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
| ممتاز لمحتوى «شخص يتكلم» القصير (ريلز، شورتس، تيك توك) | الوضع الكامل: ~10–15 دقيقة من عمل الوكيل لكل ريل (مقاس على 4 ريلز حقيقية) ويستهلك من حدّ الاستخدام |
| كل شيء قابل للتعديل لاحقًا لأنه كود | ضعيف مع المونتاج السينمائي أو متعدد الكاميرات أو المعتمد على لقطات خارجية كثيرة |
| لا تكلفة إضافية فوق اشتراك Claude | التفريغ الصوتي للهجات يحتاج مراجعة (المهارة تُلزم Claude بتصحيحه) |
| دعم قوي للعربية (اتجاه RTL، خطوط، كابشنز) | يحتاج تثبيت أدوات أول مرة؛ عمودي 9:16 فقط، مقطع واحد، بلا موسيقى خلفية بعد |

**الخلاصة:** استخدم الوضع `quick` للنشر اليومي، والوضع الكامل للفيديوهات المهمة. وراجع دائمًا قبل النشر.

### الفكرة والمصدر

الفكرة مستوحاة من فيديو [«Claude Opus 5.5 منتج الفيديو ده بالكامل من برومت واحد»](https://www.youtube.com/watch?v=CJT-5n5qffQ) لقناة **مدرسة الذكاء الاصطناعي** ([صفحة الموارد](https://arabianaischool.com/claude-reel-editing/)).
الفرق: الفيديو يستخدم برومت طويل لمرة واحدة بأسلوب ثابت؛ هذا المشروع يحوّله إلى **مهارة قابلة لإعادة الاستخدام** بأوضاع وأساليب قابلة للتبديل، مع فحص مسبق وسكربت يحسب نقاط القص بدقة الإطار.

---

## English

### Install

```bash
# prerequisites: Node.js 22+, FFmpeg, Python + faster-whisper (downloads a ~3 GB model on first run)
python3 -m venv ~/.venvs/reel && ~/.venvs/reel/bin/pip install faster-whisper
# optional, for the free local quick mode: Ollama (https://ollama.com)
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
│   ├── style-from-reference.md       # "edit it like this reel": measure, distill, rebuild (never copy assets)
│   └── hyperframes-notes.md          # setup fixes, lint codes that matter, fonts, audio measurement, commands
└── scripts/
    ├── preflight.sh                  # node 22+, ffmpeg (+version), python/faster-whisper, yt-dlp, ollama, HyperFrames, Chrome
    ├── plan_cuts.py                  # word timestamps (+ silences) → frame-accurate cuts, captions.srt, and a baked
    │                                 # CFR A-roll with optional voice cleanup (--bake --clean)
    ├── build_reel.py                 # quick mode: generates the whole HyperFrames index.html (no hand-written HTML)
    └── local_assist.py               # quick mode decisions from a local Ollama model, validated against the transcript
```

All scripts are stdlib-only and self-tested: `python3 skills/reel-editor/scripts/<script>.py --selftest`.

### Honest expectations

Good for short talking-head content. Measured on 4 real reels: ~10–15 min of agent time per full-mode reel after setup, ~1.5 min render; `quick` mode is generated by a script and can run free with a local model. Vertical 9:16, single clip, no music beds yet. Not a replacement for an editor on cinematic, multi-cam or b-roll-heavy work. Always review before posting.

### Credits

Inspired by [this video](https://www.youtube.com/watch?v=CJT-5n5qffQ) by **Arabian AI School** (مدرسة الذكاء الاصطناعي). Rendering engine and core skills: [HyperFrames](https://github.com/heygen-com/hyperframes) by HeyGen (Apache 2.0). This repo is an independent project, not affiliated with either.

MIT License.
