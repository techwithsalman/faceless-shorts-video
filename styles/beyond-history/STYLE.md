# Beyond History: Photorealistic Historical Documentary (9:16)

Cinematic, ultra-photorealistic, atmospheric historical documentaries for YouTube Shorts, TikTok, and Reels.
Features photorealistic historical figures, authentic armor and period clothing, ancient palaces, battlefields, and atmospheric chiaroscuro lighting with smooth 2.5D camera moves, drifting embers, fog mist, and documentary subtitles.

Example: `example/` = **MARCUS AURELIUS: THE STOIC EMPEROR** (180 AD; 12.8 s, 3 cinematic shots). Sheet: `style-sheet.png`.

## 1. Visual Rules
- **Photorealistic characters only.** Authentic skin pores, detailed eyes, realistic hair/beard texture, and period-accurate historical clothing/armor. No cartoon characters, stick figures, flat illustrations, or clay models.
- **Cinematic 2.5D Camera Moves.** Every scene features continuous, majestic camera motion: slow push-ins (zoom 1.0 to 1.15), macro tracking pans across armor and facial features, or low-angle crane tilts.
- **Atmospheric Effects.** Real-time procedural floating dust motes, campfire sparks, drifting mist/smoke, subtle candle flicker, and 35mm cinematic lens vignette.
- **Documentary Typography.** Classical serif font (`Caladea` / `Georgia`), cream/ivory text with dark drop shadow, and active word highlighted in imperial gold (`#F5D061`) using millisecond timings from Faster-Whisper.
- **Voiceover & Audio.** Solemn, authoritative British documentary narration (`bm_george` via local Kokoro-82M), blended with a low orchestral sub-bass drone and atmospheric whooshes/braams via `mix.py`.

## 2. Technical Pipeline
1. `script.json`: Written in serious, compelling documentary prose.
2. `voice.py`: Generates `data/narration.wav` using Kokoro `bm_george` (or `am_michael`).
3. `words.py`: Extracts exact word timestamps via local Faster-Whisper (`small.en`).
4. `src/shots.js`: Assigns photorealistic scene assets with 2.5D camera motion trajectories (`zoom`, `panX`, `panY`, `focusX`, `focusY`) and atmospheric layers.
5. `capture.mjs`: Headless Chrome captures 1080x1920 frames at 30 FPS and streams to FFmpeg for high-bitrate H.264/AAC MP4 output.
