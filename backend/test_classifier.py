import os, sys, time
sys.path.insert(0, '/app')
from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS

c = PhotoClassifier()
t0 = time.time()

base = '/app/fotos_prueba'
correct = 0
total = 0

for folder in sorted(os.listdir(base)):
    fpath = os.path.join(base, folder)
    if not os.path.isdir(fpath):
        continue
    expected_pos = int(folder.split(' -')[0])
    images = sorted(os.listdir(fpath))[:2]
    
    for img in images:
        path = os.path.join(fpath, img)
        if not os.path.isfile(path):
            continue
        
        pos, info = c.classify(path)
        total += 1
        label = INSPECTION_POSITIONS.get(pos, 'N/A') if pos else 'N/A'
        status = 'OK' if pos == expected_pos else 'FAIL'
        if pos == expected_pos:
            correct += 1
        print('  %s %s -> %s (%s, %s)' % (status, folder, label, info.get('method','?'), info.get('confidence','?')))

elapsed = time.time() - t0
print()
print('Elapsed: %.1fs' % elapsed)
print('Total: %d/%d correct (%d%%)' % (correct, total, correct*100//total if total > 0 else 0))
