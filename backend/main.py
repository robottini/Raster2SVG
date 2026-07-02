from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import cv2
from PIL import Image, ImageFilter
import numpy as np
from sklearn.cluster import KMeans
from skimage.measure import label, regionprops
import potrace
import io
import os
import re
import uuid
import asyncio

app = FastAPI()

# Task storage
tasks = {}

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend directory
# We assume the frontend folder is at the same level as backend or inside project root
# Current structure:
# /RasterSVG/backend/main.py
# /RasterSVG/frontend/index.html
# So we need to point to ../frontend

# Determine base path (handles both normal and PyInstaller bundle cases)
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    base_path = sys._MEIPASS
else:
    # Running normally
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTEND_PATH = os.path.join(base_path, "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

@app.get("/style.css", include_in_schema=False)
async def read_style():
    return FileResponse(os.path.join(FRONTEND_PATH, "style.css"))

@app.get("/script.js", include_in_schema=False)
async def read_script():
    return FileResponse(os.path.join(FRONTEND_PATH, "script.js"))

def resize_image_if_needed(image: Image.Image, max_size: int = 1000) -> Image.Image:
    width, height = image.size
    if max(width, height) > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        return image.resize((new_width, new_height), Image.Resampling.BILINEAR)
    return image

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def is_white(rgb):
    # Check if color is white (with small tolerance)
    return rgb[0] > 240 and rgb[1] > 240 and rgb[2] > 240

def is_black(rgb):
    # Check if color is black (with small tolerance)
    return rgb[0] < 15 and rgb[1] < 15 and rgb[2] < 15

def reduce_colors(image: Image.Image, n_colors: int):
    # Ensure image is RGB
    image = image.convert('RGB')
    
    # Convert to numpy array
    img_array = np.array(image)
    w, h, d = img_array.shape
    
    # Reshape for K-Means (pixels, channels)
    pixel_array = img_array.reshape((w * h, d))
    
    # Perform K-Means
    if n_colors < 1: n_colors = 1
    
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=3)
    kmeans.fit(pixel_array)
    
    # Replace pixel values with centroids
    labels = kmeans.predict(pixel_array)
    palette = kmeans.cluster_centers_.astype('uint8')
    quantized_pixels = palette[labels]
    
    # Reshape back to image dimensions
    quantized_img_array = quantized_pixels.reshape((w, h, d))
    labels_img = labels.reshape((w, h))
    
    # Prepare palette list
    hex_palette = [rgb_to_hex(color) for color in palette]
    
    return Image.fromarray(quantized_img_array), hex_palette, labels_img

def count_unique_colors(image: Image.Image) -> int:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return len(image.getcolors(maxcolors=1000000))

def generate_svg_potrace(labels: np.ndarray, palette: list, width: int, height: int, update_progress=None, exclude_white=False, exclude_black=False) -> str:
    parts = []
    # Add SVG header
    parts.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    
    total_colors = len(palette)
    print(f"Tracing {total_colors} color layers...")
    
    # 3. Vectorize each color plane
    for idx, hex_color in enumerate(palette):
        # Update progress
        if update_progress:
            # Progress from 10% to 90%
            progress = 10 + int((idx / total_colors) * 80)
            update_progress(progress, f"Vettorializzazione colore {idx + 1}/{total_colors}")

        # Check if we need to exclude this color
        rgb = hex_to_rgb(hex_color)
        if exclude_white and is_white(rgb):
            continue
        if exclude_black and is_black(rgb):
            continue

        # Create mask for this color based on labels (much faster than RGB comparison)
        # shape: (height, width) - boolean
        mask = (labels == idx)
        
        if not np.any(mask):
            continue

        # Label connected components to separate disjoint areas
        # connectivity=2 means 8-connected (diagonals count as connected)
        labeled_mask = label(mask, connectivity=2)
        regions = regionprops(labeled_mask)
        
        # Trace each connected component separately
        for region in regions:
            # region.image is the binary mask of the component (tight crop)
            # We invert it because we pass it to Potrace Bitmap which expects 
            # 0 as foreground (based on our previous logic/tests) or handles inversion internally.
            # Actually, our working logic was passing ~mask.
            # region.image is True for shape. ~region.image is False for shape.
            component_mask = region.image
            
            # Trace with Potrace
            bmp = potrace.Bitmap(~component_mask)
            
            # Trace
            # turdsize=4 removes small specks
            # alphamax=1 optimizes curves
            path = bmp.trace(turdsize=4, alphamax=1)
            
            # Get offset for this region
            min_row, min_col, _, _ = region.bbox
            # min_row is y, min_col is x
            
            # Build path data
            d_parts = []
            for curve in path:
                start = curve.start_point
                d_parts.append(f"M {start.x + min_col},{start.y + min_row}")
                
                for segment in curve:
                    end = segment.end_point
                    if segment.is_corner:
                        c = segment.c
                        d_parts.append(f"L {c.x + min_col},{c.y + min_row} L {end.x + min_col},{end.y + min_row}")
                    else:
                        c1 = segment.c1
                        c2 = segment.c2
                        d_parts.append(f"C {c1.x + min_col},{c1.y + min_row} {c2.x + min_col},{c2.y + min_row} {end.x + min_col},{end.y + min_row}")
                
                d_parts.append("Z") 
            
            if d_parts:
                d_str = " ".join(d_parts)
                # Add path with fill color
                # shape-rendering="crispEdges" ensures no gaps between adjacent shapes of different colors
                parts.append(f'<path d="{d_str}" fill="{hex_color}" stroke="none" shape-rendering="crispEdges" />')

    parts.append('</svg>')
    return "".join(parts)

def process_image_task(task_id: str, image_bytes: bytes, colors: int, smoothing: str, exclude_white: bool, exclude_black: bool):
    try:
        tasks[task_id] = {"status": "processing", "progress": 0, "message": "Starting..."}
        
        # Read image
        image = Image.open(io.BytesIO(image_bytes))
        
        # 1. Resize
        tasks[task_id].update({"progress": 5, "message": "Resizing..."})
        resized_image = resize_image_if_needed(image, max_size=1000)
        
        # Convert to CV2 (BGR)
        img_cv = cv2.cvtColor(np.array(resized_image), cv2.COLOR_RGB2BGR)

        # 2. Pre-processing: Denoising & Simplification
        tasks[task_id].update({"progress": 10, "message": "Denoising & Smoothing..."})
        
        # Determine parameters based on smoothing mode
        if smoothing == "aggressive":
            d = 15
            sigma = 75
            ksize = 5
        else: # light
            d = 9
            sigma = 50
            ksize = 3

        # Bilateral Filter
        img_cv = cv2.bilateralFilter(img_cv, d=d, sigmaColor=sigma, sigmaSpace=sigma)
        
        # Simplification: Median Blur
        img_cv = cv2.medianBlur(img_cv, ksize)

        # Convert back to PIL RGB for K-Means
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        preprocessed_image = Image.fromarray(img_rgb)

        # 3. Reduce Colors (K-Means)
        tasks[task_id].update({"progress": 30, "message": "Riduzione colori..."})
        # Note: K-Means can be slow too, but we don't have a progress callback for it easily
        # We could run it in a thread if needed, but here we just run it synchronously in the background task
        processed_image, palette, labels = reduce_colors(preprocessed_image, colors)
        
        # 4. Final Polish: Median Blur on labels
        tasks[task_id].update({"progress": 60, "message": "Final Polish..."})
        # Apply Median Blur to labels to smooth regions
        # labels is (w, h) int32 usually, need uint8 for cv2
        labels_uint8 = labels.astype(np.uint8)
        labels_polished = cv2.medianBlur(labels_uint8, 5)
        labels = labels_polished
        
        # Verify color count
        # unique_colors = count_unique_colors(processed_image)
        
        # Define progress updater
        def update_progress(p, msg):
            tasks[task_id].update({"progress": p, "message": msg})

        # 3. Vectorize
        svg_content = generate_svg_potrace(labels, palette, processed_image.width, processed_image.height, update_progress=update_progress, exclude_white=exclude_white, exclude_black=exclude_black)

        tasks[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Done",
            "result": {
                "svg": svg_content,
                "palette": palette
            }
        }

    except Exception as e:
        print(f"Task failed: {e}")
        tasks[task_id] = {
            "status": "error",
            "progress": 0,
            "message": str(e)
        }

@app.post("/convert")
async def convert_image(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    colors: int = Form(...),
    smoothing: str = Form("light"),
    excludeWhite: bool = Form(False),
    excludeBlack: bool = Form(False)
):
    # Create unique task ID
    task_id = str(uuid.uuid4())
    
    # Read file
    image_bytes = await file.read()
    
    # Start background task
    background_tasks.add_task(process_image_task, task_id, image_bytes, colors, smoothing, excludeWhite, excludeBlack)
    
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
