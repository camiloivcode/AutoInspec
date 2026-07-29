import os, json, cv2, numpy as np

base = '/app/fotos_prueba'

for folder in sorted(os.listdir(base)):
    folder_path = os.path.join(base, folder)
    if not os.path.isdir(folder_path):
        continue
    images = sorted(os.listdir(folder_path))[:3]
    folder_results = []
    for img_name in images:
        path = os.path.join(folder_path, img_name)
        img = cv2.imread(path)
        if img is None:
            continue
        h, w, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        color_std = float(np.std(img))
        edges = cv2.Canny(gray, 50, 150)
        edge_pct = float(np.mean(edges > 0)) * 100
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        sat_mean = float(np.mean(hsv[:,:,1]))
        hue_mean = float(np.mean(hsv[:,:,0]))
        blue_ratio = float(np.mean(img[:,:,0] > 150))
        green_ratio = float(np.mean(img[:,:,1] > 150))
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        folder_results.append({
            "file": img_name[:40],
            "dims": f"{w}x{h}",
            "brightness": round(brightness, 1),
            "color_std": round(color_std, 1),
            "edge_pct": round(edge_pct, 1),
            "sat_mean": round(sat_mean, 1),
            "hue_mean": round(hue_mean, 1),
            "blue_ratio": round(blue_ratio, 3),
            "green_ratio": round(green_ratio, 3),
            "laplacian_var": round(laplacian_var, 1),
        })
    if not folder_results:
        continue
    avg = {k: round(sum(r[k] for r in folder_results if isinstance(r[k], (int, float))) / len(folder_results), 1)
           for k in ["brightness", "color_std", "edge_pct", "sat_mean", "hue_mean", "blue_ratio", "green_ratio", "laplacian_var"]}
    print(f"\n=== {folder} ===")
    print(f"  Samples: {len(folder_results)}")
    for r in folder_results:
        print(f"  [{r['dims']}] b={r['brightness']} cs={r['color_std']} ep={r['edge_pct']}% sat={r['sat_mean']} hue={r['hue_mean']} blue={r['blue_ratio']} green={r['green_ratio']} lap={r['laplacian_var']}")
    print(f"  AVG: b={avg['brightness']} cs={avg['color_std']} ep={avg['edge_pct']}% sat={avg['sat_mean']} hue={avg['hue_mean']} blue={avg['blue_ratio']} green={avg['green_ratio']} lap={avg['laplacian_var']}")
