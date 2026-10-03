# Spoken edit cues

Creators often direct the edit out loud while recording: "cut this shot", "zoom on my face here", "put my website here", "split the screen". Treat those sentences as instructions to the editor, not as content — but notice that in a demo ("watch, I can ask it to zoom…") the instruction *is* the content, and the viewer should see it happen as it's said.

## Find them

After correcting the transcript, scan for imperative or desire phrasing aimed at the editor or the AI:

| Language | Typical phrasing |
|---|---|
| Arabic | اقطع / احذف / شيل هذه اللقطة، أريد زوم، قرّب على وجهي، ابعد الزوم، اعرض / أظهر … هنا، قسّم الشاشة / الصورة نصفين، ضع … في الأعلى/الأسفل، أريد منه أن … |
| English | cut this, delete that take, zoom in on my face, pull back slowly, put X here / up here, split the screen, show my website, add my logo |

Third-person references to the speaker ("zoom on *his* face", "وجهه") are normal — the speaker is addressing the editor.

Deictic words ("here", "هنا", "في هذا المكان") need the picture: check the contact sheet at that timestamp for where the speaker points (left/right, up/down from their own position) and place the element there.

## Execute them

| Cue | Execute | Keep the spoken sentence? |
|---|---|---|
| "cut this shot / delete this" | remove the referenced stretch (usually the dead air or retake around the cue) **and the cue sentence itself**, via `plan_cuts.py --cut a-b` | no |
| "zoom in on my face … then slowly pull back" | punch/push on the inner camera wrapper at the words, origin on the face; slow ease back on "slowly" | yes if it's a demo, no if it's a private note |
| "show X here" (name, logo, image, website) | overlay card at the pointed position, entering on the noun; capture/copy the asset locally first | yes |
| "split the screen: me at the bottom, X on top" | clip the A-roll to the bottom half (face re-centred inside it), X fills the top half; dialogue never stops. A card already on screen can grow into the half (shared-element handoff). | yes |
| "add some info about X" | a designed info card (title + 3–5 modules built one by one); content must be true — take it from the project/README, never invent | yes |

When a cue is ambiguous in a way that changes the edit (which shot is "this shot"? which website?), pick the most likely reading from the picture and the transcript and say what you chose in the report; ask only if it's genuinely a coin flip. For "my website" use the URL the user gave, or one you already know from the project or memory — otherwise ask.

Log every cue in `source-analysis.md`: time, literal words, interpretation, execution.
