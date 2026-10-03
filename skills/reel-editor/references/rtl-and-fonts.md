# RTL text and fonts (Arabic, Hebrew, Persian, Urdu)

Broken Arabic is the fastest way to make an edit look amateur: disconnected letters, reversed word order, or a fallback font mid-word. Rendering happens in a headless browser, so these rules are about making the browser do the right thing.

## Choose a font that actually exists

1. If the user supplied `fonts/`, use those files via `@font-face` with local `url()`s.
2. Otherwise discover installed fonts — don't assume. macOS/Linux: `fc-list :lang=ar family` / `fc-match Cairo` (or `system_profiler SPFontsDataType` on macOS). Don't trust `document.fonts.check()` for this: it returns `true` for any family with no `@font-face` rule, even one that doesn't exist. For `@font-face` fonts, `(await document.fonts.load('700 64px "Cairo"')).length > 0` is the real check; for system fonts, rely on the OS listing and the visual check below.
3. Preference order for Arabic display/captions, using the first one genuinely available: Cairo, Tajawal, Noto Kufi Arabic, Noto Sans Arabic, IBM Plex Sans Arabic, then system fallbacks (Geeza Pro / SF Arabic on macOS, Segoe UI on Windows).
4. If none of the good ones exist, a free Arabic font from Google Fonts can be downloaded **once into the project folder** and loaded locally — never fetched at render time. Mention it in the report.
5. Use real weights: a true Bold/Black for keywords, Bold/SemiBold for captions, Regular/Medium for small text. Faux bold on Arabic looks smeared.
6. Write the chosen family and weights into the final report.

## Shaping and direction

- Put `dir="rtl"` and `lang="ar"` (or the right code) on every RTL text container.
- Animate whole words or whole lines. Splitting Arabic into per-letter spans breaks the joining forms — the letters stop connecting.
- Mixed text (an English product name inside an Arabic sentence) should stay in the logical order the speaker said it; wrap Latin runs in `<bdi>` or a span with `dir="ltr"` if punctuation jumps to the wrong side.
- Let lines break naturally between words; never in the middle of a word.
- Don't use `letter-spacing` on Arabic.
- Verify in the real preview at 100% that letters connect and words read in the right order before approving.

## Transcripts in dialect

Whisper tends to "correct" dialect (e.g. Egyptian, Gulf, Levantine) toward MSA or to mis-hear it, and it often transliterates English terms into Arabic letters incorrectly. When fixing `transcript.json`:

- Keep the speaker's actual words and dialect in captions — don't rewrite them into MSA.
- Write well-known English names in the form the speaker's audience expects (e.g. `Claude`, `HyperFrames`) — mixed-script captions are normal in Arabic tech content.
- Keep the timestamps when correcting text; if you merge or split words, split the time span proportionally.
