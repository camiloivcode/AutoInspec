import os, sys, time
sys.path.insert(0, '/app')

from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS

c = PhotoClassifier()
t0 = time.time()

correct = 0
total = 0
for folder in sorted(os.listdir('/app/fotos_prueba')):
    fpath = os.path.join('/app/fotos_prueba', folder)
    if not os.path.isdir(fpath):
        continue
    expected_pos = int(folder.split(' -')[0])
    for img in sorted(os.listdir(fpath)):
        path = os.path.join(fpath, img)
        if not os.path.isfile(path):
            continue
        pos, info = c.classify(path)
        total += 1
        if pos == expected_pos:
            correct += 1
        else:
            label = INSPECTION_POSITIONS.get(pos, 'N/A') if pos else 'N/A'
            print('  FAIL %s -> %s (%s, %s)' % (folder, label, info.get('method','?'), info.get('confidence','?')))

print()
print('Elapsed: %.1fs' % (time.time() - t0))
print('Total: %d/%d correct (%d%%)' % (correct, total, correct*100//total if total > 0 else 0))
