"""Beyond History Batch 02 - Master Automated Production Script
Produces EXACTLY 10 complete historical documentary Shorts sequentially.
Saves all 10 MP4s and supporting assets directly into:
C:\\Users\\HP\\Desktop\\faceless-shorts-video\\beyond-history-batch-02\\
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BATCH_DIR = ROOT_DIR / "beyond-history-batch-02"
SCRIPTS_DIR = ROOT_DIR / "scripts"

# Environment and PATH setup for office PC
for candidate in [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-essentials_build" / "bin",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-full_build" / "bin",
]:
    if candidate.exists() and str(candidate) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")

VENV_PYTHON = Path.home() / ".faceless-shorts" / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)

CACHE_DIR = Path.home() / ".faceless-shorts" / "cache"
os.environ["HF_HOME"] = str(CACHE_DIR)
os.environ["TORCH_HOME"] = str(CACHE_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR)

TOPICS = [
    {
        "id": "01",
        "title": "The Fall of the Roman Empire",
        "filename": "01-the-fall-of-the-roman-empire.mp4",
        "prefix": "01-the-fall-of-the-roman-empire",
        "voice": "bm_george",
        "speed": 1.04,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "weathered 55-year-old Roman senator in crimson toga and gold signet ring, wrinkled face, grave brown eyes, living human actor, authentic period bronze armor",
        "lines": [
            {
                "text": "In four seventy-six, the greatest empire on Earth collapsed without a single grand battle.",
                "visual": "smoke rising over marble ruins of the Roman forum at dusk, shattered Corinthian columns, burning embers, 35mm film photograph"
            },
            {
                "text": "Centuries of corruption, rampant inflation, and relentless northern migrations broke Rome from within.",
                "visual": "Visigoth and Vandal warriors marching through broken city gates, torches flickering in cold autumn mist, cinematic wide shot"
            },
            {
                "text": "Its legions withered while greedy generals traded the imperial throne for quick fortunes.",
                "visual": "ancient Roman silver denarii coins spilling across weathered mosaic palace floor, tarnished and cracked, candlelit"
            },
            {
                "text": "When a barbarian chieftain deposed the teenage emperor Romulus, nobody even resisted.",
                "visual": "young defeated Roman emperor handing over his golden imperial crown in shadowed marble palace chamber"
            },
            {
                "text": "The western realm did not fall in one night. It slowly rusted away.",
                "visual": "wide cinematic shot of a lone Roman helmet resting in weeds before the monumental Colosseum at twilight"
            },
            {
                "text": "Rome believed it was eternal. History proved that no empire survives forever.",
                "visual": "close-up of weathered Roman senator looking at burning horizon, solemn eyes reflecting firelight, photorealistic"
            }
        ]
    },
    {
        "id": "02",
        "title": "The Mystery of Cleopatra",
        "filename": "02-the-mystery-of-cleopatra.mp4",
        "prefix": "02-the-mystery-of-cleopatra",
        "voice": "bf_emma",
        "speed": 1.04,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "regal 28-year-old Ptolemaic Queen Cleopatra VII of Egypt, dark kohl-rimmed Mediterranean eyes, Greek features, royal gold diadem and pleated linen robes",
        "lines": [
            {
                "text": "Cleopatra was not Egyptian, and her greatest weapon was not beauty, but ruthless intellect.",
                "visual": "Cleopatra standing on balcony of Alexandria palace overlooking Mediterranean harbor at sunset, golden torches, photorealistic"
            },
            {
                "text": "She was the first Ptolemaic ruler to master the native Egyptian language.",
                "visual": "Cleopatra reading papyrus scrolls in the Great Library of Alexandria, marble busts and warm oil lamps, cinematic"
            },
            {
                "text": "Fluent in nine tongues, she outsmarted Rome's most dangerous generals for two decades.",
                "visual": "candlelit war room with carved wooden maps, Cleopatra strategizing with Roman scrolls and bronze compasses"
            },
            {
                "text": "When enemy legions broke her palace, she refused to be paraded in chains.",
                "visual": "heavy gilded palace doors under siege, Roman shields visible through the ornate Alexandrian archway"
            },
            {
                "text": "Whether by cobra venom or lethal poison, she died on her own terms.",
                "visual": "regal Cleopatra reclining on a gold and lapis throne holding an ornate chalice, serene expression, dramatic chiaroscuro"
            },
            {
                "text": "Her lost tomb remains undiscovered, buried deep beneath shifting coastal sands.",
                "visual": "cinematic wide shot of the Great Pyramids and Alexandrian coast under a vast starry Egyptian night sky"
            }
        ]
    },
    {
        "id": "03",
        "title": "The Great Wall of China",
        "filename": "03-the-great-wall-of-china.mp4",
        "prefix": "03-the-great-wall-of-china",
        "voice": "bm_fable",
        "speed": 1.04,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "stoic ancient Chinese Ming dynasty frontier garrison commander in lacquered scale armor and embroidered silk, weathered face, dark eyes, holding iron spear",
        "lines": [
            {
                "text": "The Great Wall is not one continuous barrier, but a vast thirteen-thousand-mile defensive network.",
                "visual": "dramatic aerial view of stone Great Wall winding over rugged misty green mountain peaks at sunrise, cinematic"
            },
            {
                "text": "Begun by Emperor Qin, it took two millennia and millions of laborers to build.",
                "visual": "ancient stone masons hoisting massive granite blocks along a sheer cliff face under moody clouds, photorealistic"
            },
            {
                "text": "Signal towers relayed smoke warnings across thousands of miles in mere hours.",
                "visual": "interior of a stone watchtower, beacon fire smoking, Chinese commander surveying distant steppes through arrow slits"
            },
            {
                "text": "Yet the massive stone barricade could not stop determined nomadic armies.",
                "visual": "row of distant mountaintop beacon towers bursting with bright orange flames against twilight skies"
            },
            {
                "text": "In sixteen forty-four, a traitor opened the Shanhai Pass gate without a siege.",
                "visual": "massive iron-studded wooden fortress gate creaking open at Shanhai Pass in cold dawn light, armored guards"
            },
            {
                "text": "The greatest stone shield on Earth was ultimately defeated by human betrayal.",
                "visual": "cinematic wide silhouette of the Great Wall fading into mountain fog, timeless epic monument"
            }
        ]
    },
    {
        "id": "04",
        "title": "The Viking Age - Warriors of the North",
        "filename": "04-the-viking-age-warriors-of-the-north.mp4",
        "prefix": "04-the-viking-age-warriors-of-the-north",
        "voice": "am_fenrir",
        "speed": 1.03,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "fierce Norse jarl chieftain with braided blonde beard, weathered pale skin, blue eyes, iron spectacle helmet, chainmail and wolf pelt cloak",
        "lines": [
            {
                "text": "In seven ninety-three, dragon ships emerged from the northern mist to terrify medieval Europe.",
                "visual": "three carved wooden Viking longships cutting through icy crashing ocean waves in heavy fog at dawn, 35mm photograph"
            },
            {
                "text": "The raid on Lindisfarne monastery ignited three centuries of Norse expansion.",
                "visual": "Viking raiders storming a rocky English coastline, axes raised, storm clouds gathering overhead, cinematic"
            },
            {
                "text": "Viking helmets never had horns. Their real superpower was revolutionary naval engineering.",
                "visual": "detailed close-up of a Norse shipwright carving shallow oak keel on a fjord shore, authentic iron tools"
            },
            {
                "text": "Shallow longships could conquer open oceans and strike hundreds of miles inland.",
                "visual": "Viking longships gliding down a misty European river past burning riverside fortresses, torchlight reflection"
            },
            {
                "text": "They were fearless navigators and traders who established kingdoms from Ireland to Russia.",
                "visual": "Norse chieftain holding a glowing crystalline sunstone against overcast northern skies, fur cloak blowing"
            },
            {
                "text": "Long before Columbus, these northern warriors reached the shores of North America.",
                "visual": "cinematic close-up of Norse jarl staring intensely, snow blowing across his wolf mantle, fierce blue eyes"
            }
        ]
    },
    {
        "id": "05",
        "title": "The Assassination of Julius Caesar",
        "filename": "05-the-assassination-of-julius-caesar.mp4",
        "prefix": "05-the-assassination-of-julius-caesar",
        "voice": "bm_george",
        "speed": 1.03,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "55-year-old Julius Caesar, aristocratic aquiline features, bald crown crowned with laurel wreath, proud piercing gaze, white toga with broad purple border",
        "lines": [
            {
                "text": "On the Ides of March, sixty Roman senators concealed iron daggers beneath their togas.",
                "visual": "shadowy Roman senate hall of Pompey, senators whispering behind massive fluted marble columns, chiaroscuro"
            },
            {
                "text": "Julius Caesar had named himself dictator for life, pushing Rome to the brink.",
                "visual": "Julius Caesar seated upon a golden curule chair in the Senate, looking composed and authoritative, 35mm film photograph"
            },
            {
                "text": "Ignoring dark omens and his wife's nightmare, Caesar walked into the Senate unarmed.",
                "visual": "Caesar walking down a sunlit colonnade, conspirators falling in around him with concealed iron blades"
            },
            {
                "text": "The conspirators struck in unison, inflicting twenty-three savage wounds upon the floor.",
                "visual": "chaotic flurry of daggers catching torchlight, purple toga tearing as senators lunge forward, cinematic drama"
            },
            {
                "text": "Seeing his trusted friend Brutus among the blades, Caesar pulled his toga over his face.",
                "visual": "dramatic close-up of Caesar's sorrowful eyes locking onto Brutus, marble statue of Pompey soaked in crimson"
            },
            {
                "text": "The assassins thought they saved the Republic. Instead, they triggered its final death.",
                "visual": "solitary bloody iron dagger lying on cold marble floor of empty Senate hall at dusk, dramatic lighting"
            }
        ]
    },
    {
        "id": "06",
        "title": "The Secrets of Ancient Egypt",
        "filename": "06-the-secrets-of-ancient-egypt.mp4",
        "prefix": "06-the-secrets-of-ancient-egypt",
        "voice": "bm_fable",
        "speed": 1.04,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "ancient Egyptian high priest of Amun, shaved head, intense kohl-lined dark eyes, leopard skin mantle over white linen shendyt, heavy gold pectoral collar",
        "lines": [
            {
                "text": "For three millennia, the kingdom of the Nile guarded secrets that still baffle modern science.",
                "visual": "cinematic wide angle of the Great Sphinx and Pyramids of Giza illuminated by low golden desert sunlight, photorealistic"
            },
            {
                "text": "The Great Pyramid contains two million limestone blocks aligned precisely to true north.",
                "visual": "close-up of massive interlocking limestone blocks fitted with millimeter precision under blazing sun"
            },
            {
                "text": "Inside hidden crypts, sacred embalmers preserved Pharaohs for an eternal afterlife.",
                "visual": "flickering torchlit subterranean embalming chamber, linen wraps, alabaster canopic jars, mysterious shadows"
            },
            {
                "text": "Their mysterious script remained locked in silence until the discovery of the Rosetta Stone.",
                "visual": "carved hieroglyphs on sandstone temple wall illuminated by raking torchlight, revealing sacred symbols"
            },
            {
                "text": "When King Tutankhamun's tomb was opened, pure gold dazzled the twentieth century.",
                "visual": "archaeologist lantern catching the solid gold burial mask of Tutankhamun inside dark stone crypt, masterpiece"
            },
            {
                "text": "Ancient Egypt did not worship death. It mastered the art of immortality.",
                "visual": "silhouetted Egyptian high priest raising a gold ankh toward rising sun over Nile River, warm cinematic glow"
            }
        ]
    },
    {
        "id": "07",
        "title": "The Mongol Empire - Rise of Genghis Khan",
        "filename": "07-the-mongol-empire-genghis-khan.mp4",
        "prefix": "07-the-mongol-empire-genghis-khan",
        "voice": "am_onyx",
        "speed": 1.03,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "50-year-old Genghis Khan in heavy iron lamellar armor and fur-trimmed hat, weathered sun-darkened face, sharp watchful amber eyes, black beard",
        "lines": [
            {
                "text": "An exiled orphan named Temüjin rose from starvation to conquer the medieval world.",
                "visual": "lone young Mongol warrior on horseback against harsh frozen steppe under stormy gray skies, 35mm photograph"
            },
            {
                "text": "Taking the title Genghis Khan, he united fierce nomadic tribes into an unstoppable cavalry.",
                "visual": "Mongol cavalry galloping across endless grassland, firing composite bows at full gallop, dramatic motion"
            },
            {
                "text": "Each horse archer carried multiple mounts, riding eighty miles a day through freezing blizzards.",
                "visual": "sweep of countless cavalry horses crossing a misty river at dawn, battle flags whipping in icy wind"
            },
            {
                "text": "He promoted commanders on battlefield merit rather than royal blood, rewriting military tactics.",
                "visual": "Genghis Khan seated on ornate felt rug inside imperial yurt, reviewing battlefield commanders, candlelight"
            },
            {
                "text": "From China to Poland, his conquests forged the legendary Silk Road trade routes.",
                "visual": "camel caravan trekking across rolling golden sand dunes beneath towering mountain ranges, sunset light"
            },
            {
                "text": "His secret tomb remains undiscovered, hidden forever beneath the wild Eurasian steppe.",
                "visual": "cinematic sunset silhouette of Genghis Khan on a hilltop looking across endless horizons, epic composition"
            }
        ]
    },
    {
        "id": "08",
        "title": "The Titanic - The Night It Sank",
        "filename": "08-the-titanic-the-night-it-sank.mp4",
        "prefix": "08-the-titanic-the-night-it-sank",
        "voice": "bm_george",
        "speed": 1.03,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "elderly White Star Line Captain Edward Smith in naval uniform with gold rank insignia, full white beard, solemn blue eyes, captain's peaked hat",
        "lines": [
            {
                "text": "On April fourteenth, nineteen twelve, the grandest steamship on Earth charged into pitch-black waters.",
                "visual": "massive black steel hull of Titanic cutting through dead calm black ocean waters under a field of cold stars, photorealistic"
            },
            {
                "text": "Deemed unsinkable, Titanic raced at high speed despite repeated iceberg warnings.",
                "visual": "ship's bridge at night, Captain Smith looking through brass binoculars into pitch black night horizon"
            },
            {
                "text": "At eleven-forty, lookouts saw a monstrous wall of blue ice loom through the darkness.",
                "visual": "towering dark iceberg emerging like a shadow out of moonless ocean right beside ship's bow, cinematic"
            },
            {
                "text": "The glancing blow sliced through steel plates, flooding five forward watertight compartments.",
                "visual": "cold seawater gushing violently through riveted steel hull plates into boiler room five, steam billowing"
            },
            {
                "text": "With lifeboats for barely half the passengers, heroism and heartbreak played out on freezing decks.",
                "visual": "passengers in life jackets standing on slanted wooden boat deck as distress flares ignite night sky, photorealistic"
            },
            {
                "text": "In less than three hours, the great liner vanished into the icy Atlantic.",
                "visual": "Titanic's stern rising perpendicular into the starry night sky as lights flicker out, haunting masterpiece"
            }
        ]
    },
    {
        "id": "09",
        "title": "The Dark History of the Ottoman Empire",
        "filename": "09-the-dark-history-of-the-ottoman-empire.mp4",
        "prefix": "09-the-dark-history-of-the-ottoman-empire",
        "voice": "bm_george",
        "speed": 1.03,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "45-year-old Ottoman Grand Vizier in emerald velvet kaftan with gold embroidery, jewel-encrusted tall turban, dark brooding eyes and trimmed beard",
        "lines": [
            {
                "text": "Behind the golden gates of Topkapi Palace lay a law written in royal blood.",
                "visual": "candlelit marble corridors of Topkapi Palace, intricate Iznik tiles, arched corridors draped in velvet shadows, 35mm"
            },
            {
                "text": "To stop civil wars, Sultan Mehmed codified the chilling Law of Fratricide.",
                "visual": "imperial throne room, Sultan Mehmed on gold throne with scimitar, courtiers bowing in silence, cinematic"
            },
            {
                "text": "Every new ruler was empowered to execute his own brothers to secure the throne.",
                "visual": "silhouetted royal executioners carrying silk cords through a dimly lit palace colonnade, dramatic chiaroscuro"
            },
            {
                "text": "Later dynasties confined rival heirs inside the Kafes, isolating them inside golden gilded rooms.",
                "visual": "young Ottoman prince looking out through gilded iron window grilles into courtyard, melancholy expression"
            },
            {
                "text": "Elite Janissaries held power to crown or assassinate their imperial masters.",
                "visual": "disciplined Janissary guards standing with curved kilij swords and bork headdresses at palace gate, photorealistic"
            },
            {
                "text": "Through ruthless discipline, the Ottoman Empire endured for six centuries.",
                "visual": "cinematic wide view of the Hagia Sophia and Bosphorus strait silhouetted against a crimson twilight"
            }
        ]
    },
    {
        "id": "10",
        "title": "The Lost City of Atlantis",
        "filename": "10-the-lost-city-of-atlantis.mp4",
        "prefix": "10-the-lost-city-of-atlantis",
        "voice": "bm_fable",
        "speed": 1.04,
        "lead": 0.4,
        "outro": 0.8,
        "gap": 0.25,
        "music": "tension",
        "character": "elderly Greek philosopher in ivory wool himation, weathered thoughtful face, flowing gray beard, deep reflective eyes, holding reed pen and scroll",
        "lines": [
            {
                "text": "Around three-sixty B C, Plato wrote the enduring legend of lost Atlantis.",
                "visual": "Plato sitting in ancient Athenian marble peristyle writing on papyrus scroll, olive trees under clear Greek skies, photorealistic"
            },
            {
                "text": "In his dialogues, it was a wondrous island situated beyond the Pillars of Hercules.",
                "visual": "legendary visionary bird's-eye view of Atlantis with concentric rings of sapphire water and gleaming palaces, cinematic"
            },
            {
                "text": "Plato created Atlantis not as history, but as an allegorical warning against imperial greed.",
                "visual": "ornate bronze statues of Poseidon and Atlantean warships departing marble harbor under sunny skies, masterpiece"
            },
            {
                "text": "According to myth, when the kingdom grew arrogant, the gods unleashed divine fury.",
                "visual": "dark cataclysmic storm clouds gathering over the legendary island, lightning striking golden temple spires"
            },
            {
                "text": "In one catastrophic day of earthquakes and floods, the island vanished beneath the ocean.",
                "visual": "monumental ocean tsunami crashing over marble columns and circular waterways, engulfing the mythic city, epic drama"
            },
            {
                "text": "Though philosophical fiction, Plato's tale remains humanity's most captivating ancient mystery.",
                "visual": "sunlight rays piercing down through deep turquoise ocean water onto submerged coral-covered ruins, haunting and timeless"
            }
        ]
    }
]


def log(msg):
    print(f"\n[BATCH-02] {msg}", flush=True)


def run(cmd, cwd=None, desc=""):
    if desc:
        print(f">>> {desc}...", flush=True)
    res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=os.environ, shell=isinstance(cmd, str))
    if res.returncode != 0:
        raise RuntimeError(f"Command failed (exit {res.returncode}): {cmd}")
    return res


def get_media_info(filepath):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate",
        "-of", "json", str(filepath)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(res.stdout)
    fmt = info.get("format", {})
    dur = float(fmt.get("duration", 0.0))
    size = int(fmt.get("size", 0))
    video_stream = next((s for s in info.get("streams", []) if s.get("width")), {})
    width = video_stream.get("width")
    height = video_stream.get("height")
    codec = video_stream.get("codec_name")
    fps_str = video_stream.get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, den = fps_str.split("/")
        fps = round(float(num) / float(den), 2)
    else:
        fps = float(fps_str)
    return {"duration": dur, "size": size, "width": width, "height": height, "codec": codec, "fps": fps}


def verify_decode(filepath):
    res = subprocess.run(["ffmpeg", "-v", "error", "-i", str(filepath), "-f", "null", "-"], capture_output=True, text=True)
    if res.returncode != 0 or res.stderr.strip():
        raise RuntimeError(f"FFmpeg decode verification failed for {filepath}: {res.stderr}")
    return True


def produce_single_topic(topic, idx, total):
    tid = topic["id"]
    title = topic["title"]
    prefix = topic["prefix"]
    out_mp4 = BATCH_DIR / topic["filename"]
    
    log(f"[{idx}/{total}] STARTING DOCUMENTARY {tid}: '{title}'")
    t0 = time.time()
    
    # Clean temporary scratch inside assets/ and data/
    assets_dir = BATCH_DIR / "assets"
    data_dir = BATCH_DIR / "data"
    for d in [assets_dir, data_dir]:
        for f in d.glob("*"):
            if f.is_file():
                f.unlink()
    
    # 1. Setup script.json
    script_data = {
        "title": title,
        "voice": topic["voice"],
        "speed": topic["speed"],
        "lead": topic["lead"],
        "outro": topic["outro"],
        "gap": topic["gap"],
        "music": topic["music"],
        "character": topic["character"],
        "lines": topic["lines"]
    }
    active_script = BATCH_DIR / "script.json"
    active_script.write_text(json.dumps(script_data, indent=2), encoding="utf-8")
    
    # Save permanent topic script directly in batch folder
    perm_script = BATCH_DIR / f"{prefix}_script.json"
    perm_script.write_text(json.dumps(script_data, indent=2), encoding="utf-8")
    
    # 2. Kokoro Voice Generation with exact duration targeting (32.0s - 38.0s)
    voice_py = SCRIPTS_DIR / "voice.py"
    lines_json_path = data_dir / "lines.json"
    
    for attempt in range(5):
        run([str(VENV_PYTHON), str(voice_py), str(BATCH_DIR)], desc=f"Kokoro-82M Voiceover ({script_data['voice']} x{script_data['speed']})")
        lines_info = json.loads(lines_json_path.read_text(encoding="utf-8"))
        last_line_end = lines_info["lines"][-1]["end"]
        total_est_dur = last_line_end + script_data.get("outro", 0.8)
        print(f"Measured short duration from voiceover: {total_est_dur:.2f} s")
        
        if 32.0 <= total_est_dur <= 38.5:
            print(f"Duration {total_est_dur:.2f}s is optimal (target 30-40s).")
            break
        elif total_est_dur < 32.0:
            scale = total_est_dur / 35.0
            new_speed = max(0.80, round(script_data["speed"] * scale, 2))
            print(f"Duration {total_est_dur:.2f}s is under 32s -> lowering speed from {script_data['speed']} to {new_speed} and expanding outro to 1.0s")
            script_data["speed"] = new_speed
            script_data["gap"] = 0.32
            script_data["outro"] = 1.0
            active_script.write_text(json.dumps(script_data, indent=2), encoding="utf-8")
        else:  # total_est_dur > 38.5
            scale = total_est_dur / 35.0
            new_speed = min(1.22, round(script_data["speed"] * scale, 2))
            print(f"Duration {total_est_dur:.2f}s is over 38.5s -> increasing speed from {script_data['speed']} to {new_speed}")
            script_data["speed"] = new_speed
            script_data["gap"] = 0.20
            script_data["outro"] = 0.6
            active_script.write_text(json.dumps(script_data, indent=2), encoding="utf-8")

    # Update permanent script copy with the final tuned timing parameters
    perm_script.write_text(json.dumps(script_data, indent=2), encoding="utf-8")
        
    # 3. Faster-Whisper Subtitle Alignment
    words_py = SCRIPTS_DIR / "words.py"
    run([str(VENV_PYTHON), str(words_py), str(BATCH_DIR)], desc="Faster-Whisper Word Alignment")
    
    # 4. Local AI Image Generation with sd-turbo on CUDA
    local_image_py = SCRIPTS_DIR / "local_image.py"
    run([
        str(VENV_PYTHON), str(local_image_py),
        "--project", str(BATCH_DIR),
        "--model", "sd-turbo",
        "--width", "512",
        "--height", "768",
        "--steps", "2",
        "--character", topic["character"]
    ], desc="Local Open-Weight Image Generation (sd-turbo, 6 scenes)")
    
    # 5. Monocular Depth Estimation with Depth-Anything Small on CUDA
    depth_estimator_py = SCRIPTS_DIR / "depth_estimator.py"
    run([str(VENV_PYTHON), str(depth_estimator_py), "--project", str(BATCH_DIR)], desc="Depth-Anything Parallax Maps (CUDA)")
    
    # 6. Capture check and cues
    capture_mjs = BATCH_DIR / "tools" / "capture.mjs"
    run(["node", str(capture_mjs), "check"], cwd=BATCH_DIR, desc="Headless Chrome Scene & Timing Validation")
    run(["node", str(capture_mjs), "cues"], cwd=BATCH_DIR, desc="Sound Cue Generation")
    
    # 7. Soundtrack & Foley Mixing
    mix_py = BATCH_DIR / "tools" / "mix.py"
    run([str(VENV_PYTHON), str(mix_py), "."], cwd=BATCH_DIR, desc="Atmospheric Soundtrack & Foley Audio Mixing")
    
    # 8. Render Final MP4
    run(["node", str(capture_mjs), "video", topic["filename"]], cwd=BATCH_DIR, desc=f"Headless Chrome 1080x1920 30FPS MP4 Export -> {topic['filename']}")
    
    # 9. Render Contact Sheet
    contact_name = f"{prefix}_sheet.jpg"
    run(["node", str(capture_mjs), "sheet", contact_name, "0.5", "10"], cwd=BATCH_DIR, desc=f"QA Contact Sheet -> {contact_name}")
    
    # 10. Archive all supporting assets directly inside batch folder with prefix
    shutil.copy2(data_dir / "narration.wav", BATCH_DIR / f"{prefix}_narration.wav")
    shutil.copy2(data_dir / "lines.json", BATCH_DIR / f"{prefix}_lines.json")
    shutil.copy2(data_dir / "words.json", BATCH_DIR / f"{prefix}_words.json")
    shutil.copy2(data_dir / "cues.json", BATCH_DIR / f"{prefix}_cues.json")
    shutil.copy2(data_dir / "mix.wav", BATCH_DIR / f"{prefix}_mix.wav")
    
    for i in range(1, len(topic["lines"]) + 1):
        idx_str = f"{i:02d}"
        shutil.copy2(assets_dir / f"scene_{idx_str}.jpg", BATCH_DIR / f"{prefix}_scene_{idx_str}.jpg")
        shutil.copy2(assets_dir / f"scene_{idx_str}_depth.png", BATCH_DIR / f"{prefix}_scene_{idx_str}_depth.png")
        
    # 11. Rigorous QA Verification
    info = get_media_info(out_mp4)
    verify_decode(out_mp4)
    
    dur = info["duration"]
    w, h = info["width"], info["height"]
    fps = info["fps"]
    size_mb = info["size"] / (1024 * 1024)
    elapsed = time.time() - t0
    
    print(f"\n>>> [QA VERIFIED] {topic['filename']}:")
    print(f"    Duration: {dur:.2f} s (Target: 30-40s) -> {'PASS' if 30.0 <= dur <= 40.0 else 'FAIL'}")
    print(f"    Resolution: {w}x{h} (Target: 1080x1920) -> {'PASS' if w == 1080 and h == 1920 else 'FAIL'}")
    print(f"    Frame Rate: {fps} FPS -> {'PASS' if fps == 30.0 else 'FAIL'}")
    print(f"    Codec: {info['codec']}")
    print(f"    File Size: {size_mb:.2f} MB")
    print(f"    Render time: {elapsed:.1f} s")
    
    if not (30.0 <= dur <= 40.0):
        raise ValueError(f"Duration {dur:.2f}s is out of required 30-40s range!")
    if w != 1080 or h != 1920:
        raise ValueError(f"Resolution {w}x{h} is not 1080x1920!")
        
    return {
        "id": tid,
        "title": title,
        "filename": topic["filename"],
        "duration": dur,
        "width": w,
        "height": h,
        "fps": fps,
        "size_mb": size_mb,
        "render_time": elapsed,
        "voice": topic["voice"],
        "decode_status": "PASSED"
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Beyond History Batch 02 Automated Producer")
    ap.add_argument("--only", help="Run only specific topic ID (e.g. 01)")
    ap.add_argument("--from-id", help="Start from specific topic ID onwards")
    ap.add_argument("--dry-run", action="store_true", help="Print topic plan and exit")
    args = ap.parse_args()

    total_start = time.time()
    
    topics_to_run = TOPICS
    if args.only:
        topics_to_run = [t for t in TOPICS if t["id"] == args.only]
    elif args.from_id:
        topics_to_run = [t for t in TOPICS if int(t["id"]) >= int(args.from_id)]
        
    total_count = len(topics_to_run)
    if args.dry_run:
        print(f"Plan: {total_count} topics queued:")
        for t in topics_to_run:
            print(f"  [{t['id']}] {t['title']} -> {t['filename']}")
        return

    # Load existing summary if present to accumulate results
    summary_path = BATCH_DIR / "batch_02_summary.json"
    existing_results = {}
    if summary_path.exists():
        try:
            for item in json.loads(summary_path.read_text(encoding="utf-8")):
                existing_results[item["id"]] = item
        except Exception:
            pass

    log(f"Starting Production of Batch 02: {total_count} Historical Documentary Shorts")
    log(f"Destination: {BATCH_DIR}")

    for idx, topic in enumerate(topics_to_run, 1):
        res = produce_single_topic(topic, idx, total_count)
        existing_results[topic["id"]] = res
        # Update summary after each topic completes
        sorted_results = [existing_results[k] for k in sorted(existing_results.keys())]
        summary_path.write_text(json.dumps(sorted_results, indent=2), encoding="utf-8")

    total_elapsed = time.time() - total_start
    log(f"BATCH RUN COMPLETED: {total_count} documentary(ies) in {total_elapsed:.1f} s!")


if __name__ == "__main__":
    main()
