import os, sys, time, shutil
sys.path.insert(0, '/app')

ref_dir = '/app/ref_train'
test_dir = '/app/ref_test'
for d in [ref_dir, test_dir]:
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

holdout_paths = []

for folder in sorted(os.listdir('/app/fotos_prueba')):
    src = os.path.join('/app/fotos_prueba', folder)
    if not os.path.isdir(src):
        continue
    images = sorted(os.listdir(src))
    if len(images) < 2:
        continue
    
    dst_train = os.path.join(ref_dir, folder)
    os.makedirs(dst_train, exist_ok=True)
    
    for img in images[:-2]:
        shutil.copy2(os.path.join(src, img), os.path.join(dst_train, img))
    
    holdout_img = images[-1]
    shutil.copy2(os.path.join(src, holdout_img), os.path.join(test_dir, holdout_img))
    holdout_paths.append((folder, os.path.join(test_dir, holdout_img)))

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
    print('  %s %s -> %s (%s, %s, dist=%s)' % (status, folder, label, info.get('method','?'), info.get('confidence','?'), d))

elapsed = time.time() - t0
print()
print('Elapsed: %.1fs' % elapsed)
print('Total: %d/%d correct (%d%%)' % (correct, total, correct*100//total if total > 0 else 0))
