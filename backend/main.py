from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

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

def generate_svg_potrace(labels: np.ndarray, palette: list, width: int, height: int, update_progress=None) -> str:
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

def process_image_task(task_id: str, image_bytes: bytes, colors: int):
    try:
        tasks[task_id] = {"status": "processing", "progress": 0, "message": "Starting..."}
        
        # Read image
        image = Image.open(io.BytesIO(image_bytes))
        
        # 1. Resize
        tasks[task_id].update({"progress": 5, "message": "Resizing..."})
        resized_image = resize_image_if_needed(image, max_size=1000)
        
        # Apply Blur
        resized_image = resized_image.filter(ImageFilter.GaussianBlur(radius=1))

        # 2. Reduce Colors (K-Means)
        tasks[task_id].update({"progress": 10, "message": "Riduzione colori..."})
        # Note: K-Means can be slow too, but we don't have a progress callback for it easily
        # We could run it in a thread if needed, but here we just run it synchronously in the background task
        processed_image, palette, labels = reduce_colors(resized_image, colors)
        
        # Verify color count
        # unique_colors = count_unique_colors(processed_image)
        
        # Define progress updater
        def update_progress(p, msg):
            tasks[task_id].update({"progress": p, "message": msg})

        # 3. Vectorize
        svg_content = generate_svg_potrace(labels, palette, processed_image.width, processed_image.height, update_progress=update_progress)

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
async def start_conversion(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    colors: int = Form(...)
):
    try:
        contents = await file.read()
        task_id = str(uuid.uuid4())
        
        # Start background task
        # Note: process_image_task is a synchronous function (def), so FastAPI will run it 
        # in a thread pool, preventing it from blocking the event loop.
        background_tasks.add_task(process_image_task, task_id, contents, colors)
        
        return {"task_id": task_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
