# Riley — Voice-First AI Agent
## Product Requirements Document

**Version:** 0.1.0  
**Status:** Draft  
**Author:** Internal  

---

## 1. Overview

Riley is a voice-first AI agent that lives natively on the user's local machine. She integrates with calendar, email, messages, files, and directories to serve as a persistent, context-aware executive assistant. Riley is always available, never requires a browser tab, and operates with minimal friction — the interface gets out of the way so the user can think and act faster.

---

## 2. Vision

> "The assistant you talk to like a person, that acts like a machine."

Riley bridges the gap between natural conversation and precise computer action. She remembers context across sessions, anticipates intent from prior behavior, and executes tasks end-to-end without requiring the user to babysit each step.

---

## 3. Goals

| Priority | Goal |
|----------|------|
| P0 | Voice input and voice output with sub-300ms perceived latency |
| P0 | Local-first: runs offline, no data leaves the machine without consent |
| P0 | File and directory manipulation (read, write, move, delete, summarize) |
| P1 | Calendar integration (read events, create, modify, cancel) |
| P1 | Email integration (read, draft, send, search, label) |
| P1 | Messages integration (iMessage / SMS read and compose) |
| P2 | Long-term memory and user preference learning |
| P2 | Proactive suggestions and reminders |
| P3 | Multi-device sync |

---

## 4. Non-Goals (v1)

- Mobile-native app (v1 is desktop only)
- Third-party integrations beyond calendar / email / messages / filesystem
- Multi-user or team features
- Real-time collaboration on documents

---

## 5. Users

**Primary persona: The power user**  
A developer, founder, or knowledge worker who lives in terminals and document editors. They want to offload cognitive overhead — scheduling, drafting, summarizing — without switching context. They are comfortable granting local app permissions but are paranoid about cloud data exposure.

---

## 6. Core Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Riley UI                         │
│   Waveform / transcript strip / action confirmation     │
└────────────────┬───────────────────────────────────────-┘
                 │ voice / text
┌────────────────▼────────────────────────────────────────┐
│                  Conversation Engine                    │
│   STT → LLM (tool-calling) → TTS                       │
│   Session memory + long-term memory store               │
└──┬──────────┬──────────┬──────────┬──────────┬─────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
Calendar   Email    Messages  Filesystem  System
 Tool       Tool      Tool      Tool      Tool
```

- **STT:** Whisper (local) or streaming provider fallback  
- **LLM:** Claude claude-sonnet-4-6 via Anthropic SDK (tool-use / agentic loop)  
- **TTS:** Local (system voices / Piper) or ElevenLabs for quality  
- **Memory:** SQLite for structured facts; vector store (ChromaDB or similar) for semantic recall  
- **Tool layer:** Each integration is a discrete tool module with its own auth, schema, and test suite  

---

## 7. Feature Requirements

### 7.1 Voice Interface

| ID | Requirement |
|----|-------------|
| V-01 | Always-on wake word ("Hey Riley") with configurable alternative |
| V-02 | Push-to-talk hotkey fallback (global, configurable) |
| V-03 | Voice activity detection — auto-stop when user pauses ≥1.2s |
| V-04 | Transcript displayed in real time below waveform |
| V-05 | Riley's spoken responses surfaced as text simultaneously |
| V-06 | Interruption handling: user can start speaking mid-response to cancel it |
| V-07 | Mute toggle accessible without wake word |
| V-08 | Configurable voice persona (pitch, speed, style) |

**Edge cases:**
- Background noise above threshold → prompt user to repeat or switch to text
- Wake word fired accidentally → "Did you mean to wake me?" grace period with dismiss gesture
- Multiple audio input devices → device picker in settings, hot-swap without restart
- Microphone permission denied → graceful degradation to text-only mode with clear error

---

### 7.2 Local File & Directory Management

| ID | Requirement |
|----|-------------|
| F-01 | Read any file the user has access to (text, PDF, markdown, code) |
| F-02 | Write and overwrite files with confirmation for destructive actions |
| F-03 | Move, copy, rename, and delete with undo buffer (30s grace) |
| F-04 | Summarize files or directories on request |
| F-05 | Search file contents with natural language queries |
| F-06 | Create directory structures from verbal description |
| F-07 | Open files in the user's default application on command |
| F-08 | Watch a directory for changes and report proactively (optional) |

**Edge cases:**
- File locked by another process → report which process holds it, offer to retry
- Destructive operation on directory with >N files → require explicit verbal confirmation ("yes, delete all 47 files")
- Binary file requested as text → detect and offer to describe metadata instead
- Path contains spaces or special characters → handle transparently, never expose shell injection surface
- Symlink loops → detect and abort with clear message
- Permissions error → surface the specific permission missing, suggest `chmod` or `sudo` path
- Very large files (>100MB for text) → chunk processing, warn before loading

---

### 7.3 Calendar Integration

| ID | Requirement |
|----|-------------|
| C-01 | Read events for any time range ("what's on my calendar Thursday?") |
| C-02 | Create events with title, time, duration, location, invitees, notes |
| C-03 | Modify existing events |
| C-04 | Cancel / delete events with optional cancellation email to attendees |
| C-05 | Find free time slots given constraints ("find 90 minutes next week for a deep work block") |
| C-06 | Detect scheduling conflicts and surface them proactively |
| C-07 | Natural-language time parsing ("next Tuesday at 3", "end of next month") |
| C-08 | Multi-calendar support (work, personal, shared) |
| C-09 | Read and set reminders / alarms |

**Edge cases:**
- Ambiguous time reference ("Tuesday") when spanning a week boundary → confirm with user
- Double-booking → warn before creating, require confirmation
- Event in another timezone → normalize to local time, show original timezone
- Recurring event modification → ask scope: this event / this and future / all
- Calendar sync conflict (two devices modified same event) → surface diff and ask user to resolve
- Invitee email not found in contacts → prompt to confirm or search
- All-day event vs. timed event ambiguity → infer from phrasing, confirm for creates

---

### 7.4 Email Integration

| ID | Requirement |
|----|-------------|
| E-01 | Read inbox, sent, and arbitrary folders/labels |
| E-02 | Search email by sender, subject, date range, body content |
| E-03 | Summarize individual emails or threads |
| E-04 | Summarize unread email ("catch me up on today's email") |
| E-05 | Draft emails from verbal description |
| E-06 | Reply and forward with context from thread |
| E-07 | Send email with explicit confirmation step before dispatch |
| E-08 | Label, archive, and mark read/unread |
| E-09 | Unsubscribe from mailing lists (detect List-Unsubscribe header) |
| E-10 | Attachment awareness: describe, extract text from, or save attachments |

**Edge cases:**
- Send confirmation must survive accidental wake-word triggering ("did you say send?") — require explicit "yes send it"
- Reply-all vs. reply ambiguity → always ask when thread has >2 recipients
- Email contains sensitive content (SSN, passwords) → warn before reading aloud in full
- Attachment is an executable → refuse to open, describe only
- Email provider rate limiting → back off gracefully, surface eta
- Draft auto-save: if user walks away mid-draft → persist and resume next session
- Large mailbox search (>50k emails) → show progress indicator, allow cancel

---

### 7.5 Messages (iMessage / SMS)

| ID | Requirement |
|----|-------------|
| M-01 | Read message threads with natural language queries ("what did Alex send me?") |
| M-02 | Compose and send messages with confirmation |
| M-03 | Reply to most recent message in a thread |
| M-04 | Search messages by contact, date, or content |
| M-05 | Summarize long threads |
| M-06 | Notify user of incoming messages from priority contacts (configurable) |

**Edge cases:**
- Sending to an ambiguous contact name ("message Alex" when 3 Alexes exist) → list and ask
- Group chat reply → confirm recipient list before sending
- Message delivery failure → report and offer retry
- Contact not in address book → confirm phone number / handle before sending
- iMessage vs. SMS fallback → surface which protocol will be used

---

## 8. Memory & Context

| ID | Requirement |
|----|-------------|
| MEM-01 | Short-term: full conversation context within a session |
| MEM-02 | Long-term: user facts extracted and stored ("my work email is...", "I prefer morning meetings") |
| MEM-03 | Semantic search over past sessions for relevant context |
| MEM-04 | User can review, edit, and delete stored memories |
| MEM-05 | Memory is stored locally and encrypted at rest |
| MEM-06 | Forget command: "Riley, forget everything about [topic]" |

---

## 9. Confirmation & Safety Model

Riley follows a tiered confirmation model based on action reversibility:

| Tier | Action type | Behavior |
|------|-------------|----------|
| 0 | Read-only | Execute immediately, no confirmation |
| 1 | Reversible write (draft, label, move to trash) | Execute, report, offer undo |
| 2 | Semi-reversible (send email, send message, delete to trash) | Single verbal confirmation required |
| 3 | Irreversible (permanent delete, send to external party) | Read back full details, require "yes, confirm" |

**Undo buffer:** All Tier 1 actions are logged and reversible for 30 seconds via "Riley, undo that."

---

## 10. Privacy & Security

- All data processed locally by default; LLM API calls are the only external egress
- API key stored in system keychain, never in dotfiles or logs
- Conversation transcripts stored locally, encrypted at rest (AES-256)
- Per-integration OAuth tokens stored in system keychain
- Network requests logged; user can inspect outbound calls at any time
- "Private mode": voice captured and processed but never logged or stored
- Explicit data export and wipe in settings

---

## 11. UI Shell

The Riley UI is a minimal persistent overlay — not a full-screen app.

- **Default state:** Collapsed to a small waveform orb in a corner of the screen (configurable position)
- **Active state:** Expands to show waveform, live transcript, and action status line
- **Confirmation state:** Shows the proposed action in plain language with Yes / No / Edit options (voice or click)
- **Notification state:** Subtle pulse for incoming priority messages or proactive suggestions
- **Log panel:** Slide-in panel showing recent actions, with undo buttons
- **Settings panel:** Auth management, memory viewer, voice configuration, integration toggles

Keyboard shortcuts:
- `⌘ Space` (configurable) — toggle wake / dismiss
- `⌘ Z` — undo last action
- `⌘ ,` — open settings
- `Esc` — cancel current operation

---

## 12. Platform & Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| UI shell | Electron or Tauri | Tauri preferred (smaller footprint, Rust backend) |
| STT | OpenAI Whisper (local) | Fallback: streaming Deepgram |
| LLM | Claude via Anthropic SDK | Tool-use / agentic loop |
| TTS | Piper (local) or Kokoro | ElevenLabs optional for voice quality |
| Memory | SQLite + ChromaDB | Local, no cloud |
| Calendar | macOS EventKit / CalDAV | Windows: COM / EWS |
| Email | IMAP/SMTP + Gmail API | Modular provider adapters |
| Messages | macOS Messages.app SQLite | Sandboxing note: requires Full Disk Access |
| Filesystem | Native FS APIs | No shell passthrough to avoid injection |

---

## 13. Phased Rollout

### Phase 1 — Foundation (Weeks 1–6)
- Voice input/output loop (STT → LLM → TTS)
- Filesystem tool (read, write, search)
- Basic UI shell (orb + transcript)
- Local memory (session + simple key-value facts)

### Phase 2 — Integrations (Weeks 7–14)
- Calendar integration
- Email integration (read + draft + send)
- Messages integration (read + send)
- Confirmation model implementation
- Undo buffer

### Phase 3 — Intelligence (Weeks 15–22)
- Semantic long-term memory
- Proactive suggestions ("you have a meeting in 10 minutes and haven't sent the doc they asked for")
- Priority contact notifications
- Free-time finder and scheduling optimization

### Phase 4 — Polish & Hardening (Weeks 23–28)
- Noise handling and microphone UX
- Security audit of all integration paths
- Performance tuning (latency profiling, chunked file processing)
- Settings UI and memory inspector
- Onboarding flow

---

## 14. Open Questions

1. **Wake word engine:** Use an on-device model (Porcupine, openWakeWord) or rely on push-to-talk only for v1?
2. **Windows support timeline:** Phase 1 macOS-only, or cross-platform from day one?
3. **LLM routing:** Should long document analysis route to a cheaper model to control cost?
4. **Attachment handling:** What file types should Riley be able to edit in-place vs. read-only?
5. **Contacts sync:** Does Riley need a contacts integration, or resolve names via email/calendar lookups?
6. **Multi-account email:** Single account v1, or multi-account from the start?

---

## 15. Success Metrics

| Metric | Target |
|--------|--------|
| Wake-word to first spoken word latency | < 700ms (p95) |
| Task completion rate (voice-initiated) | > 85% without fallback to typing |
| False wake rate | < 1 per hour passive use |
| User-initiated undos | < 5% of Tier 2/3 actions (low regret rate) |
| Local-only actions (no LLM call needed) | > 20% of requests (read/nav/status) |
| Daily active use streak | > 5 days/week for retained users |

---

*End of document.*
