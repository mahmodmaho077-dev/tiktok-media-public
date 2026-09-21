#!/usr/bin/env python3
"""TikTok media bridge (Invisible Rules only).
Hosts ONE engine-rendered IR-XXX video in the public repo mahmodmaho077-dev/tiktok-media-public
and prints its verified raw URL. Refuses anything that is not an IR-XXX engine render.

usage: python3 engine/bridge.py --probe                 -> exit 0 if the repo is writable from this session
       python3 engine/bridge.py <IR-XXX> <path/to/IR-XXX.mp4>
Rules enforced here:
 - id must match ^IR-\d{3}$ and the file name must be <id>.mp4 (anything else is refused)
 - the MP4 must decode (ffprobe h264 1080x1920) and be <= 50 MB
 - remote path media/<id>-<video_md5[:8]>.mp4 ; if that path already exists it is NOT overwritten:
   it is reused only if its bytes hash identically, otherwise the run stops
 - success only after the public raw URL returns HTTP 200 with the same sha256
"""
import os, re, sys, json, base64, hashlib, subprocess, time, ssl, urllib.request, urllib.error
OWNER, REPO, BRANCH = 'mahmodmaho077-dev', 'tiktok-media-public', 'main'
_CA = os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt'
CTX = ssl.create_default_context(cafile=_CA if os.path.isfile(_CA) else None)
TOKEN = os.environ.get('TIKTOK_MEDIA_REPO_TOKEN') or os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')

def api(method, path, body=None):
    h = {'Accept': 'application/vnd.github+json', 'User-Agent': 'ir-tiktok-bridge', 'X-GitHub-Api-Version': '2022-11-28'}
    if TOKEN: h['Authorization'] = f'Bearer {TOKEN}'
    if body is not None: h['Content-Type'] = 'application/json'
    req = urllib.request.Request('https://api.github.com' + path, method=method, headers=h,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=180) as r: return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b'{}')
        except Exception: return e.code, {}

def fail(msg): print(json.dumps({'ok': False, 'error': msg})); sys.exit(1)

def probe():
    st, d = api('GET', f'/repos/{OWNER}/{REPO}')
    ok = st == 200 and not d.get('private') and (d.get('permissions') or {}).get('push') is True
    return ok, st, (d.get('message') or '')[:200]

if len(sys.argv) == 2 and sys.argv[1] == '--probe':
    ok, st, msg = probe(); print(json.dumps({'writable': ok, 'http': st, 'message': msg})); sys.exit(0 if ok else 2)
if len(sys.argv) != 3: fail('usage: bridge.py <IR-XXX> <file.mp4>')
vid, path = sys.argv[1], sys.argv[2]
if not re.fullmatch(r'IR-\d{3}', vid): fail(f'refused id {vid!r}: only IR-XXX TikTok ids are accepted')
base = os.path.basename(path)
if base != f'{vid}.mp4': fail(f'refused file {path!r}: must be the engine render named {vid}.mp4')
if not os.path.isfile(path) or os.path.getsize(path) > 50 * 1024 * 1024: fail('file missing or larger than 50 MB')
pr = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,width,height', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
if pr != 'h264,1080,1920': fail(f'not an engine render (ffprobe: {pr!r})')
vmd5 = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-map', '0:v', '-f', 'md5', '-'], capture_output=True, text=True).stdout.strip().split('=')[-1]
data = open(path, 'rb').read(); sha = hashlib.sha256(data).hexdigest()
dest = f'media/{vid}-{vmd5[:8]}.mp4'
ok, st, msg = probe()
if not ok: fail(f'bridge not writable from this session (HTTP {st}: {msg})')
st, cur = api('GET', f'/repos/{OWNER}/{REPO}/contents/{dest}?ref={BRANCH}')
if st == 200:
    remote_sha = None
else:
    st, res = api('PUT', f'/repos/{OWNER}/{REPO}/contents/{dest}', {'message': f'Add {vid} (TikTok engine render)', 'content': base64.b64encode(data).decode(), 'branch': BRANCH})
    if st not in (200, 201): fail(f'upload failed (HTTP {st}): {res.get("message")}')
url = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{dest}'
for _ in range(12):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'ir-tiktok-bridge', 'Cache-Control': 'no-cache'}), context=CTX, timeout=180) as r:
            body = r.read(); code = r.status
        if code == 200 and hashlib.sha256(body).hexdigest() == sha:
            print(json.dumps({'ok': True, 'id': vid, 'url': url, 'sha256': sha, 'video_md5': vmd5, 'bytes': len(data), 'reused_existing': st == 200})); sys.exit(0)
        if code == 200: fail(f'{dest} exists with DIFFERENT bytes; not overwriting')
    except Exception: pass
    time.sleep(10)
fail(f'public URL did not return the exact file: {url}')
