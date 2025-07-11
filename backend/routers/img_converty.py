

input_folder = "/home/collo/Downloads/mri/anonym 2025-06-24 MR PR/anonym"
output_folder = "/home/collo/Downloads/mri/converted_images"

import os
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
from PIL import Image
import numpy as np


os.makedirs(output_folder, exist_ok=True)

# === LOOP ===
for filename in os.listdir(input_folder):
    if not filename.lower().endswith(".dcm"):
        continue

    dicom_path = os.path.join(input_folder, filename)

    try:
        dcm = pydicom.dcmread(dicom_path)

        # Only process Enhanced MR Image Storage
        if dcm.get("SOPClassUID") != "1.2.840.10008.5.1.4.1.1.4.1":
            print(f"Skipping {filename}: Not an Enhanced MR Image")
            continue

        if "PixelData" not in dcm:
            print(f"Skipping {filename}: No PixelData")
            continue

        # Read pixel array
        pixel_array = dcm.pixel_array  # shape: (num_frames, height, width)

        # Apply VOI LUT if available
        if hasattr(dcm, "VOILUTSequence"):
            pixel_array = np.array([apply_voi_lut(frame, dcm) for frame in pixel_array])

        # Normalize and save each frame
        for idx, frame in enumerate(pixel_array):
            frame = ((frame - np.min(frame)) / np.ptp(frame) * 255).astype(np.uint8)
            img = Image.fromarray(frame)
            img.save(os.path.join(output_folder, f"{filename.replace('.dcm', '')}_frame{idx+1}.png"))

        print(f"✅ Processed {filename}: {pixel_array.shape[0]} frames")

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")




