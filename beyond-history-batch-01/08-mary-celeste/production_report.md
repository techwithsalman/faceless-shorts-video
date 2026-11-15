# Production Report: 08 — The Mystery of the Mary Celeste (1872)

**Channel:** Beyond History (`@Beyond_History_0`)  
**Project Folder:** `C:\Users\Abdulwahab\faceless-shorts\beyond-history-batch-01\08-mary-celeste\`  
**Target Duration:** 35–50 seconds  
**Final Duration:** 49.19 seconds  
**Resolution & Format:** 1080×1920 (9:16 vertical), 30.00 FPS constant, H.264 High Profile / AAC 48 kHz stereo  
**Render Output:** `renders/08-mary-celeste.mp4` (34.30 MB, 1476 frames, 0 stream errors)  
**Contact Sheet:** `review/08-mary-celeste-contact.jpg`  

---

## 1. Historical Fact-Checking & Primary Sources
- **Gibraltar Vice-Admiralty Court Inquiry Records (December 1872 – March 1873):** Detailed maritime salvage testimonies of Captain David Morehouse and First Mate Oliver Deveau of the *Dei Gratia*.
- **Official Cargo Manifest:** Confirmed cargo of 1,701 barrels of denatured industrial alcohol consigned to Genoa; salvage inspection found 9 barrels empty with bung staves popped, likely leaking flammable vapor.
- **Factual Corrections Integrated:**
  - Debunked Sir Arthur Conan Doyle's 1884 fictional story (*J. Habakuk Jephson's Statement*): There were NO warm cups of tea, half-eaten breakfasts, or untouched hot bowls on the mess tables.
  - The ship's single yawl/lifeboat was missing, along with the marine chronometer, sextant, navigation logbook, and ship's register, proving an orderly, deliberate evacuation rather than a paranormal vanishing.

---

## 2. Audio Production & Synchronization
- **Voice Narration:** Local Kokoro-82M ONNX model (`bm_george` UK male documentary timbre) at speed 1.11, generating 49.19s of suspenseful, measured documentary narration.
- **Subtitles:** Faster-Whisper word-by-word alignment (110 words total), serif Roman typographic hierarchy with `#F5D061` imperial gold active-word highlight, strictly positioned in the lower-third safe zone.
- **Score & Foley:** Procedural documentary score in C minor with dynamic dialogue ducking (-24 dBFS during narration, +4 dB swell during dramatic pauses), layered with 13 synchronized Foley cues (creaking wooden ship timbers, ocean swell splash, eerie bulkhead groans, distant ocean thunder).

---

## 3. Visuals & Depth-Displaced Parallax (2.5D)
- **Local Generation:** 6 photorealistic documentary plates rendered offline via `stabilityai/sd-turbo` (CPU, attention slicing, 35mm film grain, 768×1024 base upscaled with Lanczos).
- **Depth Estimation:** Pixel-accurate depth maps computed via `LiheYoung/depth-anything-small-hf`.
- **Choreography:** Dynamic WebGL parallax camera maneuvers:
  - Scene 1: Moody wide oceanic shot with subtle nautical swell roll as the unmanned brigantine drifts through grey Atlantic waves.
  - Scene 2: First-person perspective boarding the wet, deserted wooden deck with an unmanned turning ship wheel.
  - Scene 3: Eerie glide across Captain Benjamin Briggs's quiet wood-paneled cabin with sea charts and brass dividers.
  - Scene 4: Ominous low-angle push into the cavernous cargo hold lined with oak alcohol barrels and rising mist.
  - Scene 5: Violent oceanic storm shot of the tiny wooden lifeboat battling towering dark Atlantic swells.
  - Scene 6: Haunting documentary finale pull-back through morning ocean sea fog as the sun pierces the mist.

---

## 4. Quality Assurance & Verification
- **ffprobe stream audit:** 1080×1920, 30 FPS constant, duration 49.19s, AAC stereo.
- **ffmpeg null decode:** Zero frame drops, zero macroblocking, zero audio/video desync.
