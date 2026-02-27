# 🎙️ PocketMic: Strategic Pivot
## From "AI App" to "Professional Music Workspace"

### 🎵 The New Mental Model
PocketMic is no longer a "one-off generation tool." It is a **persistent music journal** where projects evolve over time. AI is the **assistant engineer**, not the performer.

---

## 🏗️ Product Flow Redesign

### 1️⃣ Project History (The Home Surface)
The default landing experience. It feels like a high-end creative vault.
- **Visuals**: A clean grid of cards. No flashy "AI" graphics.
- **Content**: Each card shows `Project Name`, `Duration`, and `Last Refined` timestamp.
- **Language**: "New Session" instead of "Record with AI."
- **Focus**: Continuity. The user sees their history as a body of work.

### 2️⃣ Project Workspace (The DAW-Lite Core)
A modular environment where the user "works" on the track.
- **Layout**: 
    - **Header**: Persistent playback bar with simplified transport (Play/Pause/Loop).
    - **Center**: High-fidelity waveform display with "Revision Marks."
    - **Modular Panels** (Expandable/Collapsible):
        - **Voice**: Pitch correction, Tone, De-esser.
        - **Beat**: Style selection, BPM, Groove intensity.
        - **Mixer**: Relative levels between Voice and Beat.
    - **Collaborator Sidebar**: Where AI suggestions live. "Suggested: Dip mid-range in beat to clarify vocals." [Apply | Modify].

### 3️⃣ Mastering Console (The Specialized Surface)
A dedicated environment for the final "Diamond" polish.
- **Manual Controls**: Big, satisfying knobs for:
    - **Loudness**: LUFS Target (-14 to -9).
    - **Character**: Saturation, Warmth, Clarity.
    - **Imaging**: Stereo Width.
    - **Dynamics**: Compression Intensity.
- **Visuals**: Professional metering (RMS vs Peak).
- **AI Integration**: "Suggested Starting Point" button. AI explains *why* it chose a specific chain based on the track's mood.

---

## 🛠️ Architecture Adjustments
1. **Versioned Project Schema**: Each project needs a `versions` table or a history of `result_plan` states to allow rolling back.
2. **Metadata-First Persistence**: Store raw parameters (EQ levels, gain settings) aside from the rendered `.wav` to make them tweakable post-generation.
3. **Stateful API**: Moving from "Fire and Forget" production to "Update and Re-render" where individual parameters can be patched.

---

## 📅 Updated Sprint Plan (Next 12 Steps)

### Sprint 6: The Foundation of Continuity
- **Project Persistence**: Migrate `Job` to a `Project` model with name/metadata editing.
- **History Revamp**: Transform `/projects` into the primary dashboard (DAW-Lite style).
- **Project Navigation**: Implement the transition from History -> Workspace.

### Sprint 7: The Workshop Environment
- **Modular Workspace**: Build the Project Workspace (`/project/[id]`) with expandable panels.
- **Waveform Timeline**: Implement a persistent audio player that stays synced across panels.
- **Parameter Control**: Connect Workspace sliders to the backend mixing/mastering engine.

### Sprint 8: The Human-in-the-Loop Mastering
- **Mastering Console UI**: Redesign the mastering page with professional metering and manual knobs.
- **AI Suggestion Engine**: Implement the "Assistant" logic that generates suggested parameters without auto-applying them.
- **Refinement Loops**: Allow users to "Re-render" specific parameters instantly.

---

## 🚫 UX Language Audit
| Old Phrase | New Phrase | Rationale |
| :--- | :--- | :--- |
| "Generate with AI" | "Create" | AI is the engine, not the intent. |
| "AI is processing..." | "Polishing..." / "Synthesizing..." | Sounds like music production, not data processing. |
| "Powered by AI" | (Remove) | Implied by project quality. |
| "Let AI create a beat" | "Suggested Beat" | Keeps user in the driver's seat. |
