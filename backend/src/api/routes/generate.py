import os
import re
import uuid
import json
import logging
import shutil
import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional

from ...infrastructure.document_generation.inspection_generator import InspectionPDFGenerator
from ...infrastructure.ocr.plate_detector import PlateDetector
from ...infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS
from .history import save_history_record

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Generate PDF"])

TEMP_DIR = "/data/uploads/temp"
OUTPUT_DIR = "/data/output"

MAX_PER_POSITION = {10: 2}


@router.post("/generate-pdf")
async def generate_pdf(
    driver_name: str = Form(...),
    plate: str = Form(...),
    images: List[UploadFile] = File(...),
    positions: List[str] = Form(...),
):
    if not driver_name.strip():
        raise HTTPException(status_code=400, detail="El nombre del conductor es obligatorio")
    if not plate.strip():
        raise HTTPException(status_code=400, detail="La placa es obligatoria")

    if len(images) != len(positions):
        raise HTTPException(status_code=400, detail="Cantidad de imágenes y posiciones no coinciden")

    counts: dict[str, int] = {}
    for pos_str in positions:
        pos = int(pos_str)
        if pos < 1 or pos > 11:
            raise HTTPException(status_code=400, detail=f"Posición inválida: {pos}")
        max_count = MAX_PER_POSITION.get(pos, 1)
        counts[pos_str] = counts.get(pos_str, 0) + 1
        if counts[pos_str] > max_count:
            label = INSPECTION_POSITIONS.get(pos, f"Posición {pos}")
            raise HTTPException(status_code=400, detail=f"La posición '{label}' acepta máximo {max_count} imagen(es)")

    session_id = str(uuid.uuid4())[:8]
    work_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(work_dir, exist_ok=True)

    try:
        image_map: dict[int, list[str]] = {}
        pos_counters: dict[int, int] = {}
        for img_file, pos_str in zip(images, positions):
            pos = int(pos_str)
            pos_counters[pos] = pos_counters.get(pos, 0) + 1
            ext = os.path.splitext(img_file.filename or "image.jpg")[1] or ".jpg"
            dest = os.path.join(work_dir, f"{pos}_{pos_counters[pos]}{ext}")
            content = await img_file.read()
            with open(dest, "wb") as f:
                f.write(content)
            image_map.setdefault(pos, []).append(dest)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        generator = InspectionPDFGenerator()
        result_path = generator.generate(
            driver_name=driver_name.strip(),
            plate=plate.strip().upper(),
            images=image_map,
            output_dir=OUTPUT_DIR,
        )

        safe_name = re.sub(r'[^\w\s-]', '', driver_name).strip().replace(' ', '_')
        filename = f"{safe_name}.pdf"
        media_type = "application/pdf" if result_path.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        try:
            file_size = os.path.getsize(result_path)
            save_history_record(
                driver_name=driver_name.strip(),
                plate=plate.strip().upper(),
                filename=filename,
                file_size=file_size,
            )
        except Exception as e:
            logger.warning(f"Failed to save history record: {e}")

        return FileResponse(result_path, media_type=media_type, filename=filename)

    except Exception as e:
        logger.exception("Error generating PDF")
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)


@router.post("/auto-analyze")
async def auto_analyze(
    images: List[UploadFile] = File(...),
):
    if not images:
        raise HTTPException(status_code=400, detail="Debe enviar al menos una imagen")

    session_id = str(uuid.uuid4())[:8]
    work_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(work_dir, exist_ok=True)

    try:
        saved_paths = []
        for img_file in images:
            safe_name = os.path.basename(img_file.filename or "image.jpg")
            dest = os.path.join(work_dir, safe_name)
            content = await img_file.read()
            with open(dest, "wb") as f:
                f.write(content)
            saved_paths.append(dest)

        plate_detector = PlateDetector()
        classifier = PhotoClassifier()

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=4) as pool:
            plate_task = loop.run_in_executor(pool, plate_detector.detect_from_multiple, saved_paths)
            classify_task = loop.run_in_executor(pool, classifier.classify_batch, saved_paths)
            suggested_plate, classification = await asyncio.gather(plate_task, classify_task)

        suggestions = []
        for path in saved_paths:
            fname = os.path.basename(path)
            result = classification.get(path, {})
            pos = result.get("position")
            info = result.get("info", {})
            suggestions.append({
                "filename": fname,
                "suggested_position": pos,
                "position_label": INSPECTION_POSITIONS.get(pos) if pos else None,
                "confidence": info.get("confidence", "low"),
            })

        return {
            "suggested_plate": suggested_plate,
            "suggestions": suggestions,
            "total_images": len(saved_paths),
        }

    except Exception as e:
        logger.exception("Error in auto-analyze")
        raise HTTPException(status_code=500, detail=f"Error analizando imágenes: {str(e)}")
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)


@router.post("/generate-pdf/auto")
async def generate_pdf_auto(
    driver_name: str = Form(...),
    plate: str = Form(...),
    images: List[UploadFile] = File(...),
    positions: List[str] = Form(...),
):
    if not driver_name.strip():
        raise HTTPException(status_code=400, detail="El nombre del conductor es obligatorio")
    if not plate.strip():
        raise HTTPException(status_code=400, detail="La placa es obligatoria")
    if len(images) != len(positions):
        raise HTTPException(status_code=400, detail="Cantidad de imágenes y posiciones no coinciden")

    counts: dict[str, int] = {}
    for pos_str in positions:
        pos = int(pos_str)
        if pos < 1 or pos > 11:
            raise HTTPException(status_code=400, detail=f"Posición inválida: {pos}")
        max_count = MAX_PER_POSITION.get(pos, 1)
        counts[pos_str] = counts.get(pos_str, 0) + 1
        if counts[pos_str] > max_count:
            label = INSPECTION_POSITIONS.get(pos, f"Posición {pos}")
            raise HTTPException(status_code=400, detail=f"La posición '{label}' acepta máximo {max_count} imagen(es)")

    session_id = str(uuid.uuid4())[:8]
    work_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(work_dir, exist_ok=True)

    try:
        image_map: dict[int, list[str]] = {}
        pos_counters: dict[int, int] = {}
        for img_file, pos_str in zip(images, positions):
            pos = int(pos_str)
            pos_counters[pos] = pos_counters.get(pos, 0) + 1
            ext = os.path.splitext(img_file.filename or "image.jpg")[1] or ".jpg"
            dest = os.path.join(work_dir, f"{pos}_{pos_counters[pos]}{ext}")
            content = await img_file.read()
            with open(dest, "wb") as f:
                f.write(content)
            image_map.setdefault(pos, []).append(dest)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        generator = InspectionPDFGenerator()
        result_path = generator.generate(
            driver_name=driver_name.strip(),
            plate=plate.strip().upper(),
            images=image_map,
            output_dir=OUTPUT_DIR,
        )

        safe_name = re.sub(r'[^\w\s-]', '', driver_name).strip().replace(' ', '_')
        filename = f"{safe_name}.pdf"
        media_type = "application/pdf" if result_path.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        try:
            file_size = os.path.getsize(result_path)
            save_history_record(
                driver_name=driver_name.strip(),
                plate=plate.strip().upper(),
                filename=filename,
                file_size=file_size,
            )
        except Exception as e:
            logger.warning(f"Failed to save history record: {e}")

        return FileResponse(result_path, media_type=media_type, filename=filename)

    except Exception as e:
        logger.exception("Error generating PDF (auto)")
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)

