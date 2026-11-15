# Beyond History AI Engine — Comprehensive Technical Audit & Architectural Improvement Plan

**Target Project:** `C:\Users\Abdulwahab\faceless-shorts`  
**Latest Video Inspected:** [`marcus-aurelius-battlefield\renders\marcus-aurelius-battlefield.mp4`](file:///C:/Users/Abdulwahab/faceless-shorts/marcus-aurelius-battlefield/renders/marcus-aurelius-battlefield.mp4)  
**Hardware Profile:** Intel Core i5-7200U (2 cores / 4 threads, 2.50 GHz), Intel HD Graphics 620 (1 GB shared VRAM), 20 GB DDR4 System RAM  
**Storage Profile:** Drive C: (2.96 GB free - CRITICALLY CONSTRAINED), Drive D: (243.85 GB free - HIGH CAPACITY), Drive E: (235.06 GB free - HIGH CAPACITY)  
**Operating Budget & APIs:** **$0.00** (Strictly 100% Free, Local, Offline Models & Tools)  
**Date:** November 14, 2026 (Audit Completed)

---

## 1. System & Project Architecture Inspection

A full source code, asset, metadata, and pipeline audit was performed on the existing codebase across `C:\Users\Abdulwahab\faceless-shorts` and its engine templates.

```
C:\Users\Abdulwahab\faceless-shorts\
├── marcus-aurelius-battlefield\
│   ├── script.json                     # Narration lines, visual descriptions, character prompt
│   ├── index.html                      # Headless DOM mount for HTML5 Canvas (1080x1920)
│   ├── src\
│   │   ├── main.js                     # Engine bootloader, asset preloader, RAF clock
│   │   ├── shots.js                    # Shot scheduling, 2.5D camera choreography, cues
│   │   └── core\
│   │       ├── timing.js               # Dual-stream timing manager (lines.json + words.json)
│   │       ├── captions.js             # Serif subtitle layout with gold word-sync highlight
│   │       ├── atmosphere.js           # Procedural canvas fog, candle flicker, drifting embers
│   │       └── lib.js                  # Math easing, lerp, clamp, coordinate transformations
│   ├── tools\
│   │   ├── capture.mjs                 # Headless Chrome runner (CDP frame-by-frame capture)
│   │   └── mix.py                      # Procedural numpy synthesizer (voice + ducking drone + SFX)
│   ├── data\
│   │   ├── narration.wav               # 42.47 s voiceover (Kokoro-82M ONNX, bm_george)
│   │   ├── lines.json                  # Line-level timestamps (7 sentences)
│   │   ├── words.json                  # 101 word-level timestamps (Faster-Whisper small.en)
│   │   ├── cues.json                   # 13 transition sound cue triggers
│   │   └── mix.wav                     # 42.47 s master audio bed (48 kHz stereo)
│   ├── assets\
│   │   ├── scene_01.jpg .. scene_07.jpg# 512x512 SD-Turbo generated JPEG stills
│   │   └── marcus_aurelius.jpg         # 768x1376 master reference portrait
│   └── renders\
│       └── marcus-aurelius-battlefield.mp4 # 42.47 s, 1080x1920, 30 FPS, H.264/AAC MP4
```

---

## 2. Technical Findings & Root-Cause Analysis

### Question 1: Why scenes look like static AI images with zoom effects

1. **Single 2D Bitmap Input per Shot**:
   - In [`src/shots.js#L51-L62`](file:///C:/Users/Abdulwahab/faceless-shorts/marcus-aurelius-battlefield/src/shots.js#L51-L62), each shot is initialized with a single static image: `let imgForShot = images[i] || images[0];`.
   - The draw routine executes `render25D(imgForShot, cam);` once per frame for the duration of that shot (5.0s to 7.0s).

2. **Classic 2D Affine Crop & Pan ("Ken Burns Effect")**:
   - Inside [`src/shots.js#L23-L32`](file:///C:/Users/Abdulwahab/faceless-shorts/marcus-aurelius-battlefield/src/shots.js#L23-L32):
     ```javascript
     const z = Math.max(zoom, 1.0);
     const srcW = image.width / z;
     const srcH = image.height / z;
     const sx = clamp(centerX - srcW / 2, 0, Math.max(0, image.width - srcW));
     const sy = clamp(centerY - srcH / 2, 0, Math.max(0, image.height - srcH));
     ctx.drawImage(image, sx, sy, srcW, srcH, 0, 0, W, H);
     ```
   - The entire "movement" is purely a 2D mathematical sub-rectangle crop (`sx, sy, srcW, srcH`) animated by `lerp(startZoom, endZoom, k)`.
   - There is **no temporal frame-to-frame synthesis**, **no vertex displacement**, and **no physical object motion**.

3. **Severe Aspect-Ratio Distortion (Square Image Stretched to 9:16)**:
   - Generated assets (`scene_01.jpg` through `scene_07.jpg`) have physical dimensions of **512 × 512 pixels** (aspect ratio 1.00:1).
   - The destination canvas is **1080 × 1920 pixels** (aspect ratio 0.5625:1).
   - In `ctx.drawImage(image, sx, sy, srcW, srcH, 0, 0, W, H)`, `srcW` and `srcH` are equal square regions, but they are mapped to `1080` (width) and `1920` (height).
   - **Result:** The image is vertically stretched by a factor of $1920 / 1080 \approx 1.777\times$. Human faces, helmets, and camps are noticeably elongated, instantly signaling to the human eye that a flat 2D picture has been digitally deformed.

4. **Asset Duplication Across Timeline**:
   - Cryptographic SHA-256 hash inspection reveals that of the 7 scenes:
     - `scene_01.jpg` and `scene_02.jpg` are identical (`B3D77DE7...`, 27,527 bytes).
     - `scene_03.jpg` and `scene_05.jpg` are identical (`81D3F195...`, 41,002 bytes).
     - `scene_04.jpg` and `scene_06.jpg` are identical (`518A2466...`, 49,547 bytes).
   - Viewers see only 4 distinct pictures over a 42-second runtime. When scene 5 cuts in, it is the exact same image as scene 3, differing only by digital zoom factor.

---

### Question 2: Why character faces and appearance are inconsistent

1. **Text-Prompt Only Conditioning Without Image Embeddings**:
   - In [`scripts/local_image.py#L148-L162`](file:///C:/Users/Abdulwahab/Downloads/faceless-shorts-20261113T163547Z-1-001/faceless-shorts/scripts/local_image.py#L148-L162), images are synthesized via standard `AutoPipelineForText2Image`.
   - The pipeline passes a descriptive text string: `"Cinematic historical documentary still, close-up photograph of weathered 50-year-old Mediterranean man with beard..."`.
   - Text diffusion models possess high latent variance. Words like "weathered man with beard" map to millions of possible facial topologies in the latent space.

2. **No Face-Lock Architecture (No IP-Adapter, LoRA, or ControlNet)**:
   - There is no image-prompt adapter (IP-Adapter) to inject the facial identity embedding vectors of a canonical reference image into the cross-attention layers.
   - There is no trained LoRA weight representing Marcus Aurelius.
   - Consequently, when the scene changes from a portrait shot to an interior command tent shot, the model synthesizes a completely different human face, different nose bridge, different hairline, and different ear geometry.

3. **Inference Distillation Trade-Off (SD-Turbo at 1-2 steps)**:
   - `sd-turbo` operates using Adversarial Diffusion Distillation (ADD) in 1 or 2 steps with `guidance_scale = 0.0`.
   - While ultra-fast on CPU, it lacks the multi-step denoising refinement (15–30 steps) required to resolve fine, consistent anatomical facial landmarks across different lighting and poses.

---

### Question 3: Why scenes lack continuous physical movement and realistic action

1. **Absence of a Video Diffusion / I2V (Image-to-Video) Backbone**:
   - The engine generates **static images**, not **video latents**.
   - Models designed for continuous physical motion—such as Stable Video Diffusion (SVD), AnimateDiff, or CogVideo—operate with 3D convolution or temporal self-attention across 14 to 25 latent frames.
   - Without a temporal diffusion pass, natural physical dynamics (flowing cloaks, breath condensing in winter air, soldier movement, wind blowing banner cloth, eyes blinking, lips moving) cannot occur.

2. **Procedural Movement is Confined to Atmospheric Canvas Overlays**:
   - In [`src/core/atmosphere.js`](file:///C:/Users/Abdulwahab/faceless-shorts/marcus-aurelius-battlefield/src/core/atmosphere.js), the only animated elements are 45 circular particles representing floating dust/embers and a sine-wave illumination flicker.
   - Because these particles float on top of a frozen bitmap, the human visual cortex immediately perceives the contrast between active foreground particles and completely frozen human characters and environments.

3. **Hardware Compute Realities**:
   - On the current home laptop (Intel Core i5-7200U, dual core, no dedicated CUDA GPU), generating a full 4-second neural video at 30 FPS would take 45–60 minutes per shot via CPU.
   - However, micro-motion, mesh warping, and layered depth parallax can run in seconds.

---

### Question 4: Why battlefield environments and camera movements lack cinematic depth

1. **Flat Single-Plane Projection**:
   - The engine renders a single 2D plane: `render25D` does not perform depth-based transformation.
   - In real cinematography, when a camera pushes into a battlefield:
     - Foreground elements (watchfire brazier, nearby soldier, snow in the foreground) traverse across the lens at high relative velocity.
     - Midground elements (command tent, horses) move at moderate velocity.
     - Background elements (distant hills across the Danube, overcast sky) remain nearly stationary.
   - In the current video, every pixel moves at identical velocity. This is planar 2D scaling, not 3D camera travel.

2. **No Depth Map Estimation**:
   - The project does not currently compute monocular depth maps (e.g., via `Depth Anything V2` or `MiDaS`).
   - Without a depth map ($Z$-buffer), the engine has no data regarding which pixels are 1 meter from the lens versus 100 meters away.

3. **Atmospheric Effects Lack Volumetric Occlusion**:
   - The mist and fog in `atmosphere.js` are applied as a uniform linear gradient overlay: `mist = ctx.createLinearGradient(0, H - 450, 0, H)`.
   - The fog does not wrap behind foreground figures or pool in landscape valleys; it merely acts as a semi-transparent wash over the bottom of the screen.

---

### Question 5: Whether narration, subtitles, sound effects, and music are properly synchronized

| Component | Synchronization Status | Technical Implementation & Validation |
| :--- | :--- | :--- |
| **Narration Speech** | ✅ **Fully Synchronized** | Kokoro-82M ONNX renders sentence-by-sentence with exact padding (`lead=0.3s`, `gap=0.22s`, `outro=0.8s`). Spoken length matches `lines.json` to within 1 millisecond. |
| **Subtitle Captions** | ✅ **Fully Synchronized** | Faster-Whisper (`small.en`) extracts exact word start/end bounds into `words.json`. `captions.js` evaluates `t >= w.s && t <= w.e + 0.08` to highlight words in imperial gold (`#F5D061`) on the exact spoken syllable. |
| **Sound Effects (SFX)** | ✅ **Sample-Accurate to Cuts** | `shots.js` emits cues at `cut(i)` and `cut(i) + 0.15`. `mix.py` maps these triggers directly to sample offsets `int(cue['t'] * SR)` in the 48 kHz stereo buffer. |
| **Music Bed & Ducking** | ✅ **Accurately Ducked** | `mix.py` runs an automatic audio ducking envelope: `m *= (1 - 0.55 * np.clip(lev * 3, 0, 1))`. When voice is detected, background tension drone drops by ~55%, recovering smoothly during inter-sentence pauses. |
| **Acoustic Quality Limitation** | ⚠️ **Synthetic vs Authentic** | Although timing synchronization is mathematically exact, the SFX in `mix.py` are purely synthetic procedural numpy waveforms (filtered white noise sweeps, sine-wave impacts). They lack organic, authentic historical textures (real sword clangs, steel armor creaks, crackling campfire logs, snow footfalls). |

---

### Question 6: Which existing local models and tools can improve these problems

All solutions listed below are **100% free, open-weight, locally runnable, and require $0.00 in API costs**.

```
+---------------------------------------------------------------------------------------------------+
|                                  LOCAL ENGINE TOOLKIT & UPGRADE MAP                               |
+---------------------------------------------------------------------------------------------------+
|  Problem Domain          |  Local Open-Weight Model / Tool          |  Resource / Cache Location  |
+--------------------------+------------------------------------------+-----------------------------+
|  1. True 9:16 Aspect     |  SD-Turbo native 576x1024 OR             |  Code fix in shots.js +     |
|     & Ken Burns Cover    |  Cover-Crop Aspect Ratio Math            |  local_image.py             |
|                          |                                          |                             |
|  2. Cinematic 2.5D Depth |  Depth Anything V2 Small (ONNX / CPU)    |  D:\faceless-shorts-ai\     |
|     & Parallax Motion    |  or MiDaS-v2.1-small (1.2s on CPU)       |  cache\depth\ (~45 MB)      |
|                          |                                          |                             |
|  3. Character Facial     |  InsightFace / ReActor / Face-Align OR   |  D:\faceless-shorts-ai\     |
|     Consistency          |  Reference-Only ControlNet (SD 1.5)      |  cache\models\              |
|                          |                                          |                             |
|  4. Continuous Physical  |  * Laptop (CPU): WebGL 2.5D Mesh Warp    |  Native browser / WebGL     |
|     Motion & Action      |  * Office PC (RTX GPU): SVD / LivePort   |  D:\faceless-shorts-ai\     |
|                          |                                          |                             |
|  5. Authentic Historical |  Curated Local Offline Foley Library     |  D:\faceless-shorts-ai\     |
|     Audio & Sound Beds   |  (fire crackle, wind, boots, armor)      |  foley\ (~60 MB WAVs)       |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Step-by-Step Improvement Plan

### Phase 1: High-ROI Architectural Fixes (Zero Extra Compute)

1. **Aspect-Ratio "Cover" Logic in Canvas (`shots.js`)**:
   - Replace the distorting `ctx.drawImage(image, sx, sy, srcW, srcH, 0, 0, W, H)` with a proper aspect-ratio "cover" calculation.
   - When given a square 512x512 image, the engine will compute the 9:16 viewport crop, completely eliminating the 1.77× vertical elongation of human faces and Roman armor.

2. **Native 9:16 Visual Generation (`local_image.py`)**:
   - Update `local_image.py` default dimensions for historical shorts from `512x512` to `576x1024` or `512x910`.
   - Both SD 1.5 and SD-Turbo support asymmetric aspect ratios without memory overhead.

3. **Guaranteed Scene De-Duplication**:
   - Update `produce_history.py` to ensure that every shot in `script.json` generates its own unique prompt and asset.
   - Prevent recycling identical images across different scenes.

---

### Phase 2: True 2.5D Monocular Depth & Multi-Plane Parallax

1. **Integrate Local Monocular Depth Estimation**:
   - Add a lightweight depth pass using `Depth Anything V2 Small` (or `MiDaS Small` ONNX, ~45 MB).
   - Runs in ~1.2 seconds per scene on the laptop CPU.
   - Outputs a 16-bit or 8-bit normalized grayscale depth map (`scene_01_depth.png`).

2. **Depth-Displaced Parallax Camera**:
   - In `shots.js`, use the depth map to displace pixels during camera movement:
     $$\Delta x = \text{panX} \cdot \left(1.0 - \text{depth}(u, v)\right)$$
   - Foreground objects shift dramatically across the screen while distant mountains remain steady, achieving genuine cinematic documentary depth.

3. **Depth-Aware Volumetric Fog**:
   - Feed the depth map into `atmosphere.js` so fog and drifting snow particles organically disperse *behind* the foreground characters.

---

### Phase 3: Character Facial Consistency Engine

1. **Canonical Master Face Reference**:
   - Establish a designated high-resolution master portrait (e.g. `assets/marcus_aurelius.jpg`).

2. **Local Face Alignment & Swapping Pass**:
   - Use an open-weight face-swapping / feature-locking module (e.g. `InsightFace` / `ReActor` ONNX) running locally on CPU.
   - After each scene image is generated, the canonical facial landmarks from the master portrait are projected onto the newly synthesized character body, guaranteeing consistent jawline, nose structure, and facial identity across all war tent and battlefield scenes.

---

### Phase 4: Motion & Action Strategy (Dual-PC Architecture)

1. **On Home PC (Laptop - CPU / Intel HD 620)**:
   - Implement **Micro-Dynamic 2.5D Motion**:
     - WebGL mesh-warp or multi-plane camera movement.
     - Dynamic lighting oscillation (breathing shadows from torches).
     - Procedural eye-focus and slow camera tilt.
     - Keeps generation time under 30 seconds per video with zero GPU requirements.

2. **On Office PC (High-End Workstation / NVIDIA RTX GPU)**:
   - Leverage **Stable Video Diffusion (SVD-XT 1.1)** or **LivePortrait**:
     - Convert each static keyframe into a 25-frame cinematic video clip (wind in hair, snow drifting across armor, natural head movement).
     - Fully supported by the automated `scripts/setup_office_pc.ps1` installer.

---

### Phase 5: Authentic Documentary Foley & Audio Enhancement

1. **Curated Offline Historical Foley Bank**:
   - Store a lightweight folder of royalty-free, authentic acoustic WAV recordings on Drive `D:\faceless-shorts-ai\foley`:
     - `wind_frozen_steppe.wav`
     - `campfire_crackling_logs.wav`
     - `roman_cuirass_leather_clank.wav`
     - `parchment_quill_write.wav`
     - `distant_war_horns.wav`

2. **Keyword-Triggered Sound Placement**:
   - In `tools/mix.py`, parse the Faster-Whisper `words.json`:
     - When word `"frozen"` or `"wind"` occurs $\rightarrow$ blend ambient howling winter wind.
     - When word `"tent"` or `"journal"` occurs $\rightarrow$ blend subtle parchment quill scratching.
     - When word `"barbarian"` or `"fought"` occurs $\rightarrow$ blend distant iron blade resonance.
   - This elevates the production from simple sine-wave beeps to professional BBC / History Channel sound design.

---

## 4. Preservation & Storage Safeguards

1. **Zero Deletions**: No existing scripts, templates, or renders will be deleted or overwritten.
2. **Drive C: Protection**: All new model weights, depth networks, and foley sound banks are strictly anchored to:
   - `D:\faceless-shorts-ai\cache` (243.8 GB free)
   - Or `E:\` (235.0 GB free)
   - Zero megabytes added to the constrained `C:` drive.
3. **Backward Compatibility**: The existing procedural engine and `sd-turbo` generation remain intact as default fallback modes.

---

*Report successfully generated and saved to [`C:\Users\Abdulwahab\faceless-shorts\AUDIT_AND_IMPROVEMENT_PLAN.md`](file:///C:/Users/Abdulwahab/faceless-shorts/AUDIT_AND_IMPROVEMENT_PLAN.md).*
