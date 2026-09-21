#!/usr/bin/env bash
# Invisible Rules video engine — one-time setup in a fresh container (npm + PyPI only; no other network needed)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p assets && cd assets
[ -f model_q8.onnx ] || {
  npm pack kokoro-q8-shards@1.0.0 kokoro-js@1.2.1 @fontsource/archivo-black@5 @fontsource/inter@5 >/dev/null 2>&1
  for f in *.tgz; do mkdir -p "${f%.tgz}"; tar -xzf "$f" -C "${f%.tgz}"; done
  cat kokoro-q8-shards-1.0.0/package/kokoro-q8.part{0,1,2,3,4,5}.bin > model_q8.onnx
  cp fontsource-archivo-black-*/package/files/archivo-black-latin-400-normal.woff2 ab.woff2
  for w in 600 700 800; do cp fontsource-inter-*/package/files/inter-latin-$w-normal.woff2 in$w.woff2; done
  cp -r kokoro-js-1.2.1/package/voices voices_raw
}
pip install -q kokoro-onnx soundfile --break-system-packages 2>/dev/null || pip install -q kokoro-onnx soundfile
python3 - <<'PY'
import numpy as np
n='af_heart'; np.savez('voices.npz', **{n: np.fromfile(f'voices_raw/{n}.bin',dtype=np.float32).reshape(510,1,256)})
import os; os.replace('voices.npz','voices.bin')
import onnxruntime as ort; s=ort.InferenceSession('model_q8.onnx', providers=['CPUExecutionProvider'])
assert [i.name for i in s.get_inputs()]==['input_ids','style','speed'], 'unexpected model inputs'
print('SETUP OK: model', os.path.getsize('model_q8.onnx'), 'bytes')
PY
