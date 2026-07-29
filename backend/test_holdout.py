import os, sys, time, json, shutil
sys.path.insert(0, '/app')

ref_dir = '/app/fotos_prueba_holdout'
if os.path.exists(ref_dir):
    shutil.rmtree(ref_dir)

os.makedirs(ref_dir, exist_ok=True)
holdout_map = {}

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
    shutil.copy2(os.path.join(src, holdout_img), os.path.join(dst, holdout_img))
    holdout_map[folder] = holdout_img
    
    for img in images[:-1]:
        shutil.copy2(os.path.join(src, img), os.path.join(dst, img))

from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS

c = PhotoClassifier(ref_dir)
t0 = time.time()

correct = 0
total = 0

for folder, holdout_img in sorted(holdout_map.items()):
    expected_pos = int(folder.split(' -')[0])
    path = os.path.join(ref_dir, folder, holdout_img)
    
    pos, info = c.classify(path)
    total += 1
    label = INSPECTION_POSITIONS.get(pos, 'N/A') if pos else 'N/A'
    status = 'OK' if pos == expected_pos else 'FAIL'
    if pos == expected_pos:
        correct += 1
    print('  %s %s -> %s (%s, %s, dist=%s)' % (status, folder, label, info.get('method','?'), info.get('confidence','?'), info.get('distance','?')))

elapsed = time.time() - t0
print()
print('Elapsed: %.1fs' % elapsed)
print('Total: %d/%d correct (%d%%)' % (correct, total, correct*100//total if total > 0 else 0))
