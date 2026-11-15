# Production Report: Pompeii — The Day the Sun Vanished (AD 79)

**Project:** `04-pompeii`  
**Channel:** Beyond History (`@Beyond_History_0`)  
**Production Status:** COMPLETED & VERIFIED (Zero Errors)  
**Render Output:** `renders/04-pompeii.mp4`  
**Contact Sheet:** `review/04-pompeii-contact.jpg`  

---

## 1. Technical Specifications
- **Resolution:** 1080 × 1920 (9:16 vertical format)
- **Frame Rate:** 30.00 FPS constant
- **Duration:** 48.90 seconds (1467 rendered frames)
- **Video Codec:** H.264 High Profile, YUV420p
- **Audio Codec:** AAC stereo, 48 kHz, 16-bit
- **File Size:** 33.80 MB (bitrate ~5.53 Mbps)
- **Integrity Validation:** `ffmpeg -v error -i renders/04-pompeii.mp4 -f null -` returned zero frame or decoding errors.

---

## 2. Historical & Narrative Audit
- **Primary Sources:**
  - Pliny the Younger, *Epistulae* VI.16 & VI.20 (letters to Tacitus recording eyewitness account of the towering umbrella-pine eruption column).
  - Giuseppe Fiorelli archaeological field reports (1863 pioneering plaster cast technique).
  - Modern volcanological and forensic thermal analyses of Mount Vesuvius pyroclastic density currents.
- **Narrative Hook:** Immediate visceral cataclysm in the first 2 seconds: low-angle volcanic lightning and colossal ash column erupting above Roman villas.
- **Fact-Checking & Factual Accuracy:**
  - Clarifies that victims caught in the direct pyroclastic surge at dawn died instantly of intense thermal shock (>300°C) rather than slow suffocation.
  - Documents the hours of daylight-blocking pumice stone rainfall preceding the lethal pyroclastic surges.
  - Portrays authentic archaeological plaster casts capturing victims in their final frozen postures.

---

## 3. Visuals, 2.5D Parallax & Sound Design
- **Visual Imagery:** 6 photorealistic historical documentary plates generated with local open-weight Stable Diffusion Turbo operating 100% offline.
- **Living Motion & Depth:** Monocular depth estimation via Depth-Anything small model running locally, displaced dynamically with camera tremors, volcanic seismic rumble, and atmospheric ash dissipation.
- **Sound Design:** 14 procedural Foley cues (deep sub rumble, volcanic slam, pumice fall slides, distant bells, triumphant brass coda) balanced beneath Kokoro-82M ONNX narration with dynamic dialogue ducking.
- **Subtitles:** Word-by-word synchronized subtitles powered by Faster-Whisper, styled in serif typography with `#F5D061` imperial gold highlight positioned safely within the lower third.
