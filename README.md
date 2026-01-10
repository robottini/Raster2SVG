# RasterSVG - Raster to SVG Converter

A modern web application to convert raster images (JPEG, PNG) into optimized SVG vectors.

## Features

- **Layer-by-Layer Conversion**: Precise vectorization, color by color.
- **Custom Palette**: Choose the number of colors (from 1 to 30) using the K-Means algorithm.
- **Superpixel & Connected Components**: Advanced handling of disjoint shapes for sharp details.
- **Modern Interface**: Clean, responsive, and intuitive UI.
- **Multilingual**: Supports English and Italian.
- **Preview & Download**: View the result and download the SVG directly.

## Local Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/RasterSVG.git
    cd RasterSVG
    ```

2.  **Create a virtual environment (recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the backend server (FastAPI):

```bash
uvicorn backend.main:app --reload
```

The application will be available at: `http://localhost:8000`

## Technologies

- **Backend**: Python, FastAPI, NumPy, Scikit-learn (K-Means), Scikit-image, Potrace.
- **Frontend**: HTML5, CSS3 (Modern), JavaScript (Vanilla).

## License

MIT
