#!/usr/bin/env python3
"""Invisible Rules video engine.
usage: python3 make_video.py story.json --check     (phonemes + caption validation only)
       python3 make_video.py story.json --preview   (+ voice, timeline, preview contact sheet)
       python3 make_video.py story.json --full      (+ full render -> <id>.mp4 + check sheet)
"""
import sys, json, re, base64, asyncio, pathlib, subprocess
E = pathlib.Path(__file__).resolve().parent
A = E / 'assets'
story_path = pathlib.Path(sys.argv[1]).resolve(); mode = sys.argv[2] if len(sys.argv) > 2 else '--preview'
ST = json.loads(story_path.read_text()); OUT = story_path.parent / ST['id']; OUT.mkdir(exist_ok=True)
GAP, TAIL, FPS = 0.28, 1.9, 30

def fail(msg): print('ERROR:', msg); sys.exit(1)

# ---------- 1. validation ----------
from kokoro_onnx import Kokoro
K = Kokoro(str(A / 'model_q8.onnx'), str(A / 'voices.bin'))
FIX = ST.get('phoneme_fixes', {})
def phon(text):
    p = K.tokenizer.phonemize(text, 'en-us')
    for a, b in FIX.items(): p = p.replace(a, b)
    return p
problems = []
for i, s in enumerate(ST['scenes']):
    words = s['vo'].split()
    if re.search(r'\d', s['vo']): problems.append(f'scene {i}: VO contains digits — spell numbers out for the voice')
    caps = s.get('captions', [])
    if s['visual']['type'] != 'rule':
        if sum(n for _, n in caps) != len(words): problems.append(f'scene {i}: captions cover {sum(n for _,n in caps)} words, VO has {len(words)}')
        for txt, _ in caps:
            if len(txt.replace('*', '')) > 26: problems.append(f'scene {i}: caption too long ({txt})')
    elif len(s['visual']['display'].split()) != len(words): problems.append(f'scene {i}: rule display words != VO words')
with open(OUT / 'phonemes.txt', 'w') as f:
    for i, s in enumerate(ST['scenes']): f.write(f"[{i}] {s['vo']}\n    {phon(s['vo'])}\n")
print((OUT / 'phonemes.txt').read_text())
if problems: fail('\n  '.join([''] + problems))
print('VALIDATION OK')
if mode == '--check': sys.exit(0)

# ---------- 2. voice + timeline ----------
import numpy as np, soundfile as sf
t = 0.0; scenes = []; caps = []; words_t = []; parts = []; sr = 24000
for i, s in enumerate(ST['scenes']):
    audio, sr = K.create(phon(s['vo']), voice=ST.get('voice', 'af_heart'), speed=ST.get('speed', 1.0), is_phonemes=True)
    d = len(audio) / sr; words = s['vo'].split()
    w = []
    for word in words:
        p = re.sub(r'[ˈˌ.,:;!?]', '', phon(word)); w.append(max(1, len(p)) + (4 if word[-1] in '.,:;!?' else 0))
    cum = np.concatenate([[0], np.cumsum(w)]) / sum(w) * d
    wt = [(words[k], round(t + cum[k], 3), round(t + cum[k + 1], 3)) for k in range(len(words))]
    words_t.append({'scene': i, 'words': wt})
    k = 0
    for txt, n in s.get('captions', []):
        caps.append({'scene': i, 'text': txt, 'start': wt[k][1], 'end': wt[k + n - 1][2]}); k += n
    last = i == len(ST['scenes']) - 1
    end = t + d + (TAIL if last else GAP)
    scenes.append({'i': i, 'start': round(t, 3), 'speech_end': round(t + d, 3), 'end': round(end, 3)})
    parts += [audio, np.zeros(int(sr * (TAIL if last else GAP)))]
    t = end
for a, b in zip(caps, caps[1:]):
    if a['scene'] == b['scene'] and b['start'] - a['end'] < 0.6: a['end'] = b['start']
sf.write(OUT / 'voice.wav', np.concatenate(parts), sr)
TL = {'duration': round(t, 3), 'scenes': scenes, 'captions': caps, 'words': words_t}
(OUT / 'timeline.json').write_text(json.dumps(TL, indent=1))
print('duration', round(t, 2), 's')
if t > 60: fail('video longer than 60s — tighten the script')

# ---------- 3. page ----------
html = (E / 'template.html').read_text()
html = html.replace('__STORY__', json.dumps(ST)).replace('__TL__', json.dumps(TL))
html = html.replace('__AVATAR__', 'data:image/png;base64,' + base64.b64encode((E / 'avatar.png').read_bytes()).decode())
page = E / f"_page_{ST['id']}.html"; page.write_text(html)

async def shoot(times, outdir):
    from playwright.async_api import async_playwright
    outdir.mkdir(exist_ok=True)
    async with async_playwright() as p:
        import os
        launch_kwargs = {'executable_path': '/opt/pw-browsers/chromium'} if os.path.exists('/opt/pw-browsers/chromium') else {}
        b = await p.chromium.launch(**launch_kwargs); pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(page.as_uri()); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(400)
        for n, tt in enumerate(times):
            await pg.evaluate(f'render({tt})'); await pg.screenshot(path=str(outdir / f'f{n:05d}.png'))
        await b.close()
    if errs: fail('page errors: ' + '; '.join(errs[:3]))

def sheet(files, labels, out, w=270, h=480, cols=6):
    from PIL import Image, ImageDraw
    rows = (len(files) + cols - 1) // cols
    s = Image.new('RGB', (cols * (w + 10) + 10, rows * (h + 34) + 10), 'white'); d = ImageDraw.Draw(s)
    for n, (f, lab) in enumerate(zip(files, labels)):
        x = 10 + (n % cols) * (w + 10); y = 10 + (n // cols) * (h + 34)
        s.paste(Image.open(f).convert('RGB').resize((w, h)), (x, y)); d.text((x + 4, y + h + 6), lab, fill='black')
    s.save(out)

# preview: start, middle and end of every scene
pts = []
for sc in scenes: pts += [sc['start'] + 0.35, (sc['start'] + sc['speech_end']) / 2, sc['speech_end'] - 0.05]
pv = OUT / 'preview'; import shutil; shutil.rmtree(pv, ignore_errors=True)
asyncio.run(shoot(pts, pv))
sheet(sorted(pv.glob('*.png')), [f't={p:.1f}s' for p in pts], OUT / 'preview.png')
print('PREVIEW:', OUT / 'preview.png')
if mode == '--preview': sys.exit(0)

# ---------- 4. full render ----------
fr = OUT / 'frames'; shutil.rmtree(fr, ignore_errors=True)
asyncio.run(shoot([n / FPS for n in range(int(t * FPS))], fr))
mp4 = OUT / f"{ST['id']}.mp4"
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(fr / 'f%05d.png'), '-i', str(OUT / 'voice.wav'),
  '-filter_complex', '[1:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11,pan=stereo|c0=c0|c1=c0[a]', '-map', '0:v', '-map', '[a]',
  '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-r', str(FPS),
  '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', str(mp4)], check=True)
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_name,width,height,channels', '-of', 'compact', str(mp4)], capture_output=True, text=True).stdout
print(probe)
ck = OUT / 'check'; shutil.rmtree(ck, ignore_errors=True); ck.mkdir()
cks = [sc['start'] + 0.5 for sc in scenes] + [t - 0.2]
for n, tt in enumerate(cks):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{tt:.2f}', '-i', str(mp4), '-frames:v', '1', str(ck / f'c{n:02d}.png')], check=True)
sheet(sorted(ck.glob('*.png')), [f'mp4 t={p:.1f}s' for p in cks], OUT / 'check.png')
shutil.rmtree(fr, ignore_errors=True)
print('DONE:', mp4)
