import os, sys, time, shutil
sys.path.insert(0, '/app')

ref_dir = '/app/ref_train'
for d in [ref_dir]:
    if os.path.exists(d):
        shutil.rmtree(d)

holdout_paths = []

for folder in sorted(os.listdir('/app/fotos_prueba')):
    src = os.path.join('/app/fotos_prueba', folder)
    if not os.path.isdir(src):
        continue
    images = sorted(os.listdir(src))
    if len(images) < 2:
        continue
    dst = os.path.join(ref_dir, folder)
    os.makedirs(dst, exist_ok=True)
    holdout_img = images[-1]
    for img in images[:-1]:
        shutil.copy2(os.path.join(src, img), os.path.join(dst, img))
    holdout_paths.append((folder, os.path.join(src, holdout_img)))

from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS

c = PhotoClassifier(ref_dir)
t0 = time.time()

correct = 0
total = 0
for folder, path in holdout_paths:
    expected_pos = int(folder.split(' -')[0])
    pos, info = c.classify(path)
    total += 1
    label = INSPECTION_POSITIONS.get(pos, 'N/A') if pos else 'N/A'
    status = 'OK' if pos == expected_pos else 'FAIL'
    if pos == expected_pos:
        correct += 1
    d = info.get('distance','?')
    m = info.get('method','?')
    print('  %s %s -> %s (%s, %s, dist=%s)' % (status, folder, label, m, info.get('confidence','?'), d))

print()
print('Elapsed: %.1fs' % (time.time() - t0))
print('Total: %d/%d correct (%d%%)' % (correct, total, correct*100//total if total > 0 else 0))
