"""
Upload vehicle images from backend/data/vehicle_images to Supabase Storage.
Story: CD-20.5
"""

import asyncio
import json
import mimetypes
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.storage import storage


async def upload_vehicle_images() -> None:
    images_root = Path(__file__).parent.parent / "data" / "vehicle_images"
    output_map = Path(__file__).parent.parent / "data" / "vehicle_image_upload_map.json"

    if not images_root.exists():
        raise FileNotFoundError(f"Missing image folder: {images_root}")

    uploaded = []
    failed = []

    for vehicle_folder in sorted(images_root.iterdir()):
        if not vehicle_folder.is_dir():
            continue
        for image_file in sorted(vehicle_folder.iterdir()):
            if image_file.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue

            file_path = f"{vehicle_folder.name}/{image_file.name}"
            content_type = mimetypes.guess_type(image_file.name)[0] or "application/octet-stream"

            try:
                content = image_file.read_bytes()
                result = await storage.upload_file(
                    bucket="vehicles",
                    file_path=file_path,
                    file_content=content,
                    content_type=content_type,
                )
                uploaded.append({"local": str(image_file), "bucket_path": file_path, "url": result.get("url")})
                print(f"Uploaded: {file_path}")
            except Exception as exc:
                failed.append({"local": str(image_file), "bucket_path": file_path, "error": str(exc)})
                print(f"Failed: {file_path} -> {exc}")

    output_map.write_text(json.dumps({"uploaded": uploaded, "failed": failed}, indent=2), encoding="utf-8")
    print(f"Done. Uploaded={len(uploaded)} Failed={len(failed)}")
    print(f"Upload map: {output_map}")


if __name__ == "__main__":
    asyncio.run(upload_vehicle_images())
