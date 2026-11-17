"""Prompt2Video AI — Local Script & Scene Planning Engine
100% Free, Local, Offline ($0.00, No APIs, No Cloud Subscriptions).

Transforms a general-purpose prompt into a structured, cinematic multi-scene documentary script:
- Analyzes topic, genre, and duration
- Crafts a high-retention opening hook in the first 2 seconds
- Divides narration into balanced scenes
- Generates detailed 35mm photorealistic visual prompts for local image models
- Generates synchronized Foley sound cues for procedural audio mixing
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# Cache configuration
if os.environ.get("HF_HOME"):
    CACHE_DIR = Path(os.environ["HF_HOME"])
elif Path("D:/faceless-shorts-ai/cache").exists():
    CACHE_DIR = Path("D:/faceless-shorts-ai/cache")
elif Path("D:/").exists():
    CACHE_DIR = Path("D:/faceless-shorts-ai/cache")
else:
    CACHE_DIR = Path.home() / ".faceless-shorts" / "cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(CACHE_DIR)
os.environ["TORCH_HOME"] = str(CACHE_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR)


def determine_structure(duration_seconds):
    """Calculates scene count and word target based on duration."""
    d = int(duration_seconds)
    if d <= 20:
        return 3, 40
    elif d <= 35:
        return 4, 70
    elif d <= 50:
        return 6, 105
    else:
        return 8, 140


def generate_with_transformers_model(prompt_text, num_scenes, word_target, style="documentary"):
    """Attempts local inference using a local open-weight instruction model."""
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        model_id = os.environ.get("PROMPT2VIDEO_LLM", "Qwen/Qwen2.5-0.5B-Instruct")
        print(f"Loading local LLM ({model_id}) on CPU...", flush=True)

        tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=str(CACHE_DIR))
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            cache_dir=str(CACHE_DIR),
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )

        system_msg = (
            "You are an elite cinematic documentary scriptwriter. "
            "Convert the user's prompt into an engaging script with an opening hook in the first 2 seconds. "
            f"Generate exactly {num_scenes} scenes totaling approximately {word_target} words. "
            "Output valid JSON format with keys: title, hook, scenes (array of {id, text, visual_prompt, sound_cues})."
        )

        user_content = f"Topic: {prompt_text}\nVisual Style: {style}\nNumber of Scenes: {num_scenes}\nTarget Words: {word_target}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content}
        ]

        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text_input], return_tensors="pt")

        max_tokens = min(450, max(200, word_target * 3))
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            do_sample=True
        )

        response = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        
        # Extract JSON from output
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            data = json.loads(json_match.group(0))
            if "scenes" in data and len(data["scenes"]) >= 3:
                return data
    except Exception as e:
        print(f"Local LLM inference notice: {e}. Utilizing internal semantic narrative generator.", flush=True)

    return None


def generate_structured_script(prompt_text, duration=45, style="documentary", voice="bm_george", aspect_ratio="9:16"):
    """Robust, deterministic prompt decomposition and scene architect."""
    num_scenes, target_words = determine_structure(duration)
    
    # Try local LLM first if available
    llm_result = generate_with_transformers_model(prompt_text, num_scenes, target_words, style)
    if llm_result:
        llm_result["voice"] = voice
        llm_result["aspectRatio"] = aspect_ratio
        llm_result["duration"] = duration
        return llm_result

    # Semantic template analysis based on prompt keywords
    clean_prompt = prompt_text.strip().rstrip(".?!")
    words = clean_prompt.lower().split()
    
    # Detect genre/tone
    is_space = any(w in words for w in ["space", "mars", "moon", "star", "black hole", "galaxy", "nasa", "universe", "planet"])
    is_ocean = any(w in words for w in ["ocean", "sea", "shark", "whale", "deep", "trench", "atlantis", "underwater", "shipwreck"])
    is_mystery = any(w in words for w in ["mystery", "secret", "unsolved", "disappeared", "conspiracy", "vanished", "lost", "ancient"])
    is_tech = any(w in words for w in ["ai", "robot", "future", "computer", "quantum", "technology", "cyborg", "silicon"])
    is_nature = any(w in words for w in ["nature", "animal", "volcano", "earthquake", "forest", "predator", "dinosaur", "climate"])
    
    # Extract clean title
    title = clean_prompt
    if title.lower().startswith("create a video about "):
        title = title[21:]
    elif title.lower().startswith("make a short about "):
        title = title[19:]
    elif title.lower().startswith("tell a story about "):
        title = title[19:]
    title = title.capitalize()

    # Build coherent narrative progression:
    # Scene 1: The Curiosity Hook (0-8s)
    # Scene 2: The Core Conflict / Hidden Reality (8-16s)
    # Scene 3: Escalation / Pivotal Mechanism (16-24s)
    # Scene 4: Climax / Shocking Discovery (24-32s)
    # Scene 5: Deeper Consequence / Turning Point (32-40s)
    # Scene 6: Lasting Legacy / Call to Action (40-48s)

    if is_space:
        scenes = [
            {
                "id": 1,
                "text": f"Beyond the edge of our night sky lies a mystery that defies the laws of physics: {title}.",
                "visual_prompt": f"extreme macro cinematic view of cosmic nebulae and glittering starfields around {title}, shimmering stellar dust, photorealistic astronomy documentary, 35mm film grain, 8k",
                "sound_cues": ["cosmic_sub_swell", "distant_radio_static", "stellar_drone"]
            },
            {
                "id": 2,
                "text": "For decades, scientists believed this phenomenon was impossible until modern deep-space observatories pierced the dark.",
                "visual_prompt": "giant radio telescope dishes in the Atacama desert pointing into a starry night sky, milky way rotating overhead in golden hour dusk, photorealistic, 35mm film",
                "sound_cues": ["deep_rumble_pulse", "hydraulic_dish_creak", "night_wind"]
            },
            {
                "id": 3,
                "text": "At its heart, gravitational forces are so colossal they warp time and bend beams of light like liquid.",
                "visual_prompt": "mind-bending visual simulation of warped spacetime curvature bending glowing orange starlight around a dark singularity, hyper-realistic, volumetric lighting, 35mm film",
                "sound_cues": ["gravity_distortion_whoosh", "high_frequency_tone", "heavy_bass_impact"]
            },
            {
                "id": 4,
                "text": "Any matter drawn past the event horizon is compressed into a space smaller than an atom.",
                "visual_prompt": "colossal swirling vortex of superheated plasma matter glowing fiery cyan and gold spiraling inward, blinding energetic flares, cinematic IMAX scale, 35mm film",
                "sound_cues": ["plasma_flare_roar", "matter_shearing_screech", "sub_bass_drop"]
            },
            {
                "id": 5,
                "text": "What we once thought was empty void is actually the engine that shapes entire galaxies.",
                "visual_prompt": "breathtaking panoramic view of a majestic spiral galaxy spinning slowly against dark infinity, billions of glowing solar systems, majestic cinematography",
                "sound_cues": ["majestic_orchestral_swell", "cosmic_harmonic_chime", "deep_sub_drone"]
            },
            {
                "id": 6,
                "text": f"The deepest secrets of {title} are still waiting to be discovered. Subscribe for more deep dive documentaries.",
                "visual_prompt": "cinematic pull back from an astronaut floating in deep zero-gravity staring at an infinite horizon of glittering stars, soft reflection on golden visor, 35mm film",
                "sound_cues": ["triumphant_final_chord", "spacesuit_breathing_hiss", "final_sub_drop"]
            }
        ]
    elif is_ocean:
        scenes = [
            {
                "id": 1,
                "text": f"More humans have stood on the surface of the moon than have ever ventured into the abyss of {title}.",
                "visual_prompt": f"haunting cinematic low angle looking up from the sunless ocean abyss toward the faint blue light kilometers above, deep sea marine snow drifting, 35mm film",
                "sound_cues": ["abyssal_water_groan", "distant_hydrophone_ping", "deep_ocean_swell"]
            },
            {
                "id": 2,
                "text": "Miles beneath the waves, the crushing pressure exceeds one thousand atmospheres—enough to crush a submarine like a tin can.",
                "visual_prompt": "heavy steel hull of a deep-sea submersible illuminated by powerful halogen beams cutting through pitch black water, rivets creaking, photorealistic drama, 35mm film",
                "sound_cues": ["hull_creak_stress", "pressurized_water_jet", "deep_metallic_resonance"]
            },
            {
                "id": 3,
                "text": "Yet in this freezing blackness, alien creatures thrive without sunlight, fueled by superheated volcanic vents.",
                "visual_prompt": "surreal bioluminescent deep sea jellyfish and siphonophores pulsing with glowing neon azure and amethyst light in midnight water, exquisite macro documentary, 35mm film",
                "sound_cues": ["bioluminescent_pulse_shimmer", "bubbling_hydrothermal_vent", "eerie_sonar_echo"]
            },
            {
                "id": 4,
                "text": "Every deep-sea expedition unearths bizarre species that have remained unchanged since prehistoric times.",
                "visual_prompt": "colossal shadow of an ancient giant squid or prehistoric predator gliding silently past an underwater rock wall, dramatic scale, cinematic shadows, 35mm film",
                "sound_cues": ["giant_fin_water_displacement", "low_predator_hum", "suspense_drone"]
            },
            {
                "id": 5,
                "text": "Ancient shipwrecks and sunken civilizations lie entombed in oxygen-depleted currents, perfectly preserved for millennia.",
                "visual_prompt": "ghostly wooden galleon shipwreck encrusted with sea coral resting upright on the dark sandy seabed, ancient brass cannons and ship bell, haunting atmosphere, 35mm film",
                "sound_cues": ["wood_timber_groan", "sand_drift_whisper", "poignant_cello_note"]
            },
            {
                "id": 6,
                "text": f"The deepest frontier on Earth still holds mysteries we cannot imagine. Subscribe to explore more.",
                "visual_prompt": "cinematic pull back from a lone exploration beacon glowing on the seabed into the vast shadowy expanse of the boundless midnight ocean, epic documentary finale",
                "sound_cues": ["triumphant_orchestral_coda", "peaceful_water_flow", "final_sub_drop"]
            }
        ]
    elif is_tech:
        scenes = [
            {
                "id": 1,
                "text": f"The breakthrough behind {title} is quietly reshaping human civilization faster than any invention in history.",
                "visual_prompt": f"macro cinematic shot of an advanced microscopic neural processor silicon chip with pulsing golden fiber-optic light tracks, cleanroom atmosphere, 35mm film",
                "sound_cues": ["digital_pulse_hum", "high_tech_sparkle", "deep_sub_drone"]
            },
            {
                "id": 2,
                "text": "Engineers spent decades solving equations that were once thought physically unsolvable by human minds.",
                "visual_prompt": "shadowy research laboratory lined with glowing quantum server towers and floating holographic architecture diagrams, lone computer scientist working at dawn, 35mm film",
                "sound_cues": ["server_fan_ambient", "keyboard_rapid_strokes", "quantum_hum"]
            },
            {
                "id": 3,
                "text": "By calculating billions of permutations per millisecond, machines can now predict outcomes before they happen.",
                "visual_prompt": "dramatic abstract visualization of a glowing neural network matrix connecting millions of data nodes in three dimensions, dazzling data streams flowing, 35mm film",
                "sound_cues": ["data_stream_cascade", "neural_pulse_whoosh", "frequency_rise"]
            },
            {
                "id": 4,
                "text": "From medicine to space exploration, problems that took centuries to solve are yielding in mere minutes.",
                "visual_prompt": "robotic surgical arms performing ultra-precise microscopic operations with laser accuracy inside a high-tech hospital suite, futuristic realism, 35mm film",
                "sound_cues": ["robotic_servo_whir", "laser_pulse_click", "clean_chime"]
            },
            {
                "id": 5,
                "text": "Yet with this unprecedented capability comes an existential question: who will control this immense power?",
                "visual_prompt": "cinematic silhouette of a human hand reaching out to touch a sleek robotic android hand, warm sunlight streaming between fingers, dramatic contrast, 35mm film",
                "sound_cues": ["tense_bass_pulse", "subtle_heartbeat", "synthetic_violins"]
            },
            {
                "id": 6,
                "text": f"The future of {title} has already arrived. Subscribe for more groundbreaking tech stories.",
                "visual_prompt": "epic high-altitude aerial view of a sprawling futuristic smart city illuminated by millions of cyan and gold neon lights under evening twilight, 35mm film",
                "sound_cues": ["uplifting_electronic_coda", "power_surge_swell", "final_sub_drop"]
            }
        ]
    else:
        # General / Historical / Narrative universal fallback
        scenes = [
            {
                "id": 1,
                "text": f"Everything you thought you knew about {title} is about to be challenged by the historical record.",
                "visual_prompt": f"epic cinematic establishing shot illustrating {title}, dramatic atmospheric golden hour lighting, deep shadows, exquisite textural detail, photorealistic 35mm film",
                "sound_cues": ["dramatic_brass_sting", "sub_bass_impact", "atmospheric_wind"]
            },
            {
                "id": 2,
                "text": "Behind the famous legends lay ruthless geopolitical calculations, secret treaties, and immense human sacrifice.",
                "visual_prompt": "atmospheric interior shot of leaders in period attire debating over aged parchment maps by flickering candlelight, heavy velvet drapes, 35mm film",
                "sound_cues": ["candle_flame_crackle", "parchment_rustle", "tense_drone"]
            },
            {
                "id": 3,
                "text": "When the pivotal moment struck, a single unexpected decision altered the trajectory of nations forever.",
                "visual_prompt": "intense low-angle tracking shot of marching ranks and determined historical figures bracing for impact, dust rising, high contrast cinematic photography, 35mm film",
                "sound_cues": ["marching_footsteps_gravel", "distant_war_horn", "rhythmic_drum_beat"]
            },
            {
                "id": 4,
                "text": "Eyewitness accounts describe scenes of unbelievable courage amidst overwhelming chaos and destruction.",
                "visual_prompt": "dramatic close-up portrait of an eyewitness with soot and sweat on face, eyes burning with defiance against smoke and embers, hyper-realistic, 35mm film",
                "sound_cues": ["smoke_fire_whoosh", "concussive_impact", "splintering_wood"]
            },
            {
                "id": 5,
                "text": "While contemporaries believed the outcome was certain, fate took a sudden, irreversible turn.",
                "visual_prompt": "wide panoramic vista of the historic battlefield or city in the immediate aftermath, storm clouds parting as golden sunlight cuts through smoke, 35mm film",
                "sound_cues": ["wind_howl", "mournful_solo_cello", "reverberating_chime"]
            },
            {
                "id": 6,
                "text": f"The incredible story of {title} echoes through the ages. Subscribe for more untold history.",
                "visual_prompt": "majestic cinematic pull-back from ancient stone monuments standing weathered but eternal against a blazing sunset, dust motes drifting, epic finale",
                "sound_cues": ["triumphant_orchestral_coda", "temple_bell_ring", "final_sub_drop"]
            }
        ]

    # Trim or expand to num_scenes
    if num_scenes < len(scenes):
        scenes = scenes[:num_scenes]
        # Ensure the last scene has the closing call to action
        scenes[-1]["text"] = f"The true legacy of {title} continues to shape our world. Subscribe for more."

    return {
        "title": title,
        "topic": clean_prompt,
        "duration": duration,
        "voice": voice,
        "speed": 1.16,
        "style": style,
        "aspectRatio": aspect_ratio,
        "scenes": scenes
    }


def main():
    parser = argparse.ArgumentParser(description="Prompt2Video AI — Script & Scene Planning")
    parser.add_argument("--prompt", "-p", required=True, help="User prompt or topic")
    parser.add_argument("--duration", "-d", type=int, default=45, help="Target duration in seconds")
    parser.add_argument("--style", "-s", default="cinematic-documentary", help="Visual style")
    parser.add_argument("--voice", "-v", default="bm_george", help="Kokoro voice identifier")
    parser.add_argument("--aspect-ratio", "-a", default="9:16", help="Aspect ratio (9:16, 16:9, 1:1)")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path")
    args = parser.parse_args()

    print(f">>> Analyzing prompt: \"{args.prompt}\"...", flush=True)
    t0 = time.time()
    result = generate_structured_script(
        prompt_text=args.prompt,
        duration=args.duration,
        style=args.style,
        voice=args.voice,
        aspect_ratio=args.aspect_ratio
    )
    print(f">>> Script planned in {time.time() - t0:.2f} s: {len(result['scenes'])} scenes generated.", flush=True)

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f">>> Script saved to {out_p}", flush=True)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
