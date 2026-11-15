# Production Report: The Terracotta Army — The Secret Underground Empire

**Project:** `03-terracotta-army`  
**Channel:** Beyond History (`@Beyond_History_0`)  
**Production Status:** COMPLETED & VERIFIED (Zero Errors)  
**Render Output:** `renders/03-terracotta-army.mp4`  
**Contact Sheet:** `review/03-terracotta-army-contact.jpg`  

---

## 1. Technical Specifications
- **Resolution:** 1080 × 1920 (9:16 vertical format)
- **Frame Rate:** 30.00 FPS constant
- **Duration:** 45.96 seconds (1379 rendered frames)
- **Video Codec:** H.264 High Profile, YUV420p
- **Audio Codec:** AAC stereo, 48 kHz, 16-bit
- **File Size:** 31.92 MB (bitrate ~5.55 Mbps)
- **Integrity Validation:** `ffmpeg -v error -i renders/03-terracotta-army.mp4 -f null -` returned zero frame or decoding errors.

---

## 2. Historical & Narrative Audit
- **Primary Sources:**
  - Sima Qian, *Records of the Grand Historian* (*Shiji*, Book 6, *The Basic Annals of Qin Shi Huang*).
  - Shaanxi Provincial Archaeological Institute excavation field reports (1974–present).
  - UNESCO World Heritage Site documentation: Mausoleum of the First Qin Emperor.
- **Narrative Hook:** Instant visual discovery of life-sized terracotta warrior face emerging from dry loess clay beneath a farmer's shovel within the first 1.5 seconds.
- **Fact-Checking & Myth-Busting:**
  - Accurately details that all 8,000+ discovered warriors boast individual facial features, hairstyles, armor clasps, and cheekbones.
  - Highlights the central, unexcavated tumulus containing described underground models of rivers of liquid mercury (corroborated by high soil mercury anomalies detected by modern geologists).
  - Preserves Qin Dynasty cultural aesthetics: Emperor Qin Shi Huang depicted in authentic black and crimson imperial silk robes and beaded *mianguan* headdress.

---

## 3. Visuals, 2.5D Parallax & Sound Design
- **Visual Imagery:** 6 custom-generated photorealistic historical plates rendered with local open-weight Stable Diffusion Turbo running 100% offline.
- **Living Motion & Depth:** Depth-Anything monocular depth fields projected into a WebGL displacement mesh with dynamic camera zooms, drifting dust motes, and light beams.
- **Sound Design:** 12 synchronized procedural Foley cues (shovel strike on clay, excavation earth crumble, palace drum, flowing liquid mercury shimmer) dynamically mixed under Kokoro-82M ONNX narration with automated dialogue ducking.
- **Subtitles:** Word-by-word synchronized subtitles powered by Faster-Whisper, styled in classical serif typography with `#F5D061` imperial gold highlight placed safely above YouTube Shorts UI overlays.
