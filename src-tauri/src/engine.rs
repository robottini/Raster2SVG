use image::imageops::FilterType;
use std::collections::HashSet;
use std::ffi::{c_double, c_int, c_ulong, c_void};

const MAX_IMAGE_SIZE: u32 = 1000;
#[cfg(test)]
const MAX_PREVIEW_SIZE: u32 = 220;
const KMEANS_ITERATIONS: usize = 10;
const LABEL_POLISH_RADIUS: u32 = 2;
const POTRACE_STATUS_OK: c_int = 0;
const POTRACE_CURVETO: c_int = 1;
const POTRACE_CORNER: c_int = 2;
const POTRACE_TURNPOLICY_MINORITY: c_int = 4;

#[repr(C)]
struct PotraceProgress {
    callback: Option<unsafe extern "C" fn(c_double, *mut c_void)>,
    data: *mut c_void,
    min: c_double,
    max: c_double,
    epsilon: c_double,
}

#[repr(C)]
struct PotraceParam {
    turdsize: c_int,
    turnpolicy: c_int,
    alphamax: c_double,
    opticurve: c_int,
    opttolerance: c_double,
    progress: PotraceProgress,
}

#[repr(C)]
struct PotraceBitmap {
    w: c_int,
    h: c_int,
    dy: c_int,
    map: *mut c_ulong,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct PotraceDPoint {
    x: c_double,
    y: c_double,
}

#[repr(C)]
struct PotraceCurve {
    n: c_int,
    tag: *mut c_int,
    c: *mut [PotraceDPoint; 3],
}

#[repr(C)]
struct PotracePath {
    area: c_int,
    sign: c_int,
    curve: PotraceCurve,
    next: *mut PotracePath,
    childlist: *mut PotracePath,
    sibling: *mut PotracePath,
    priv_path: *mut c_void,
}

#[repr(C)]
struct PotraceState {
    status: c_int,
    plist: *mut PotracePath,
    priv_state: *mut c_void,
}

unsafe extern "C" {
    fn potrace_param_default() -> *mut PotraceParam;
    fn potrace_param_free(param: *mut PotraceParam);
    fn potrace_trace(param: *const PotraceParam, bitmap: *const PotraceBitmap)
        -> *mut PotraceState;
    fn potrace_state_free(state: *mut PotraceState);
}

#[derive(Debug)]
pub struct QuantizedImage {
    pub width: u32,
    pub height: u32,
    pub palette: Vec<[u8; 3]>,
    pub labels: Vec<usize>,
}

#[derive(Clone, Copy, Debug)]
struct ColorF {
    r: f32,
    g: f32,
    b: f32,
}

impl ColorF {
    fn from_rgb(rgb: [u8; 3]) -> Self {
        Self {
            r: rgb[0] as f32,
            g: rgb[1] as f32,
            b: rgb[2] as f32,
        }
    }

    fn to_rgb(self) -> [u8; 3] {
        [
            self.r.round().clamp(0.0, 255.0) as u8,
            self.g.round().clamp(0.0, 255.0) as u8,
            self.b.round().clamp(0.0, 255.0) as u8,
        ]
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum SmoothingMode {
    Light,
    Aggressive,
}

impl SmoothingMode {
    fn from_str(value: &str) -> Self {
        if value.eq_ignore_ascii_case("aggressive") {
            Self::Aggressive
        } else {
            Self::Light
        }
    }

    fn radius(self) -> u32 {
        match self {
            Self::Light => 1,
            Self::Aggressive => 2,
        }
    }

    fn color_threshold_sq(self) -> i32 {
        match self {
            Self::Light => 48 * 48,
            Self::Aggressive => 78 * 78,
        }
    }
}

pub fn quantize_image_bytes(
    image_bytes: &[u8],
    colors: u8,
    smoothing: &str,
) -> Result<QuantizedImage, String> {
    let decoded = image::load_from_memory(image_bytes).map_err(|err| err.to_string())?;
    let rgb = decoded.to_rgb8();
    let (width, height) = resized_dimensions(rgb.width(), rgb.height(), MAX_IMAGE_SIZE);
    let resized = if width == rgb.width() && height == rgb.height() {
        rgb
    } else {
        image::imageops::resize(&rgb, width, height, FilterType::Triangle)
    };

    let pixels = resized
        .pixels()
        .map(|pixel| [pixel[0], pixel[1], pixel[2]])
        .collect::<Vec<_>>();
    let smoothing_mode = SmoothingMode::from_str(smoothing);
    let smoothed_pixels = smooth_rgb_pixels(&pixels, width, height, smoothing_mode);

    let requested_colors = colors.clamp(1, 30) as usize;
    let (palette, labels) = kmeans_quantize(&smoothed_pixels, requested_colors)?;
    let labels = polish_labels(&labels, width, height, palette.len(), LABEL_POLISH_RADIUS);

    Ok(QuantizedImage {
        width,
        height,
        palette,
        labels,
    })
}

#[cfg(test)]
pub fn quantized_preview_svg(
    image: &QuantizedImage,
    source_name: &str,
    smoothing: &str,
    exclude_white: bool,
    exclude_black: bool,
) -> String {
    let (preview_width, preview_height) =
        resized_dimensions(image.width, image.height, MAX_PREVIEW_SIZE);
    let mut parts = vec![
        format!(
            r#"<svg width="{}" height="{}" viewBox="0 0 {} {}" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">"#,
            image.width, image.height, preview_width, preview_height
        ),
        format!(
            r#"<!-- RasterSVG Rust quantized preview; source="{}"; smoothing="{}" -->"#,
            escape_xml(source_name),
            escape_xml(smoothing)
        ),
    ];

    for y in 0..preview_height {
        let source_y = ((y as u64 * image.height as u64) / preview_height as u64) as u32;
        let mut x = 0;
        while x < preview_width {
            let label = preview_label(image, x, y, preview_width, preview_height, source_y);
            let mut run_width = 1;

            while x + run_width < preview_width
                && preview_label(
                    image,
                    x + run_width,
                    y,
                    preview_width,
                    preview_height,
                    source_y,
                ) == label
            {
                run_width += 1;
            }

            let color = image.palette[label];
            if !should_skip_color(color, exclude_white, exclude_black) {
                parts.push(format!(
                    r#"<rect x="{x}" y="{y}" width="{run_width}" height="1" fill="{}" />"#,
                    rgb_to_hex(color)
                ));
            }

            x += run_width;
        }
    }

    parts.push("</svg>".to_string());
    parts.join("")
}

pub fn potrace_svg(
    image: &QuantizedImage,
    source_name: &str,
    smoothing: &str,
    exclude_white: bool,
    exclude_black: bool,
) -> Result<String, String> {
    let mut parts = vec![
        format!(
            r#"<svg width="{}" height="{}" viewBox="0 0 {} {}" xmlns="http://www.w3.org/2000/svg">"#,
            image.width, image.height, image.width, image.height
        ),
        format!(
            r#"<!-- RasterSVG Potrace flat path output; source="{}"; smoothing="{}" -->"#,
            escape_xml(source_name),
            escape_xml(smoothing)
        ),
    ];

    for label in 0..image.palette.len() {
        let color = image.palette[label];
        if should_skip_color(color, exclude_white, exclude_black) {
            continue;
        }

        let traced_paths = trace_label(image, label)?;
        if traced_paths.is_empty() {
            continue;
        }

        let d = traced_paths.join(" ");
        parts.push(format!(
            r#"<path d="{}" fill="{}" stroke="none" shape-rendering="crispEdges" />"#,
            d,
            rgb_to_hex(color)
        ));
    }

    parts.push("</svg>".to_string());
    Ok(parts.join(""))
}

pub fn palette_to_hex(palette: &[[u8; 3]]) -> Vec<String> {
    palette.iter().map(|color| rgb_to_hex(*color)).collect()
}

fn resized_dimensions(width: u32, height: u32, max_size: u32) -> (u32, u32) {
    let longest = width.max(height);
    if longest <= max_size {
        return (width.max(1), height.max(1));
    }

    if width >= height {
        let new_width = max_size;
        let new_height = ((height as f32 * (max_size as f32 / width as f32)).round() as u32).max(1);
        (new_width, new_height)
    } else {
        let new_height = max_size;
        let new_width = ((width as f32 * (max_size as f32 / height as f32)).round() as u32).max(1);
        (new_width, new_height)
    }
}

fn kmeans_quantize(
    pixels: &[[u8; 3]],
    colors: usize,
) -> Result<(Vec<[u8; 3]>, Vec<usize>), String> {
    if pixels.is_empty() {
        return Err("Image has no pixels".to_string());
    }

    let unique_pixels = unique_pixels(pixels);
    let cluster_count = colors.min(unique_pixels.len()).max(1);
    let mut centroids = initial_centroids(&unique_pixels, cluster_count);
    let mut labels = vec![0; pixels.len()];

    for _ in 0..KMEANS_ITERATIONS {
        let mut sums = vec![[0_f64; 3]; centroids.len()];
        let mut counts = vec![0_u32; centroids.len()];

        for (index, pixel) in pixels.iter().enumerate() {
            let label = nearest_centroid(*pixel, &centroids);
            labels[index] = label;
            sums[label][0] += pixel[0] as f64;
            sums[label][1] += pixel[1] as f64;
            sums[label][2] += pixel[2] as f64;
            counts[label] += 1;
        }

        for (index, centroid) in centroids.iter_mut().enumerate() {
            if counts[index] == 0 {
                continue;
            }

            let count = counts[index] as f32;
            centroid.r = (sums[index][0] as f32) / count;
            centroid.g = (sums[index][1] as f32) / count;
            centroid.b = (sums[index][2] as f32) / count;
        }
    }

    for (index, pixel) in pixels.iter().enumerate() {
        labels[index] = nearest_centroid(*pixel, &centroids);
    }

    let palette = centroids.into_iter().map(ColorF::to_rgb).collect();
    Ok((palette, labels))
}

fn smooth_rgb_pixels(
    pixels: &[[u8; 3]],
    width: u32,
    height: u32,
    mode: SmoothingMode,
) -> Vec<[u8; 3]> {
    let radius = mode.radius();
    let threshold_sq = mode.color_threshold_sq();
    let mut output = vec![[0, 0, 0]; pixels.len()];

    for y in 0..height {
        let y0 = y.saturating_sub(radius);
        let y1 = (y + radius).min(height - 1);

        for x in 0..width {
            let x0 = x.saturating_sub(radius);
            let x1 = (x + radius).min(width - 1);
            let center = pixels[(y * width + x) as usize];
            let mut sums = [0_u32; 3];
            let mut count = 0_u32;

            for ny in y0..=y1 {
                for nx in x0..=x1 {
                    let neighbor = pixels[(ny * width + nx) as usize];
                    if rgb_distance_sq(center, neighbor) <= threshold_sq {
                        sums[0] += neighbor[0] as u32;
                        sums[1] += neighbor[1] as u32;
                        sums[2] += neighbor[2] as u32;
                        count += 1;
                    }
                }
            }

            if count == 0 {
                output[(y * width + x) as usize] = center;
            } else {
                output[(y * width + x) as usize] = [
                    (sums[0] / count) as u8,
                    (sums[1] / count) as u8,
                    (sums[2] / count) as u8,
                ];
            }
        }
    }

    output
}

fn polish_labels(
    labels: &[usize],
    width: u32,
    height: u32,
    palette_size: usize,
    radius: u32,
) -> Vec<usize> {
    if labels.is_empty() || palette_size == 0 {
        return labels.to_vec();
    }

    let mut output = vec![0; labels.len()];

    for y in 0..height {
        let y0 = y.saturating_sub(radius);
        let y1 = (y + radius).min(height - 1);

        for x in 0..width {
            let x0 = x.saturating_sub(radius);
            let x1 = (x + radius).min(width - 1);
            let mut counts = vec![0_u16; palette_size];

            for ny in y0..=y1 {
                for nx in x0..=x1 {
                    let label = labels[(ny * width + nx) as usize];
                    if label < counts.len() {
                        counts[label] += 1;
                    }
                }
            }

            let original = labels[(y * width + x) as usize];
            let mut best_label = original;
            let mut best_count = counts.get(original).copied().unwrap_or(0);

            for (label, count) in counts.into_iter().enumerate() {
                if count > best_count {
                    best_count = count;
                    best_label = label;
                }
            }

            output[(y * width + x) as usize] = best_label;
        }
    }

    output
}

fn rgb_distance_sq(a: [u8; 3], b: [u8; 3]) -> i32 {
    let dr = a[0] as i32 - b[0] as i32;
    let dg = a[1] as i32 - b[1] as i32;
    let db = a[2] as i32 - b[2] as i32;
    dr * dr + dg * dg + db * db
}

fn trace_label(image: &QuantizedImage, label: usize) -> Result<Vec<String>, String> {
    let mut bitmap = PotraceBitmapBuffer::new(image.width, image.height)?;
    let mut has_pixels = false;

    for y in 0..image.height {
        for x in 0..image.width {
            let index = (y * image.width + x) as usize;
            if image.labels[index] == label {
                bitmap.set(x, y);
                has_pixels = true;
            }
        }
    }

    if !has_pixels {
        return Ok(Vec::new());
    }

    unsafe {
        let param = potrace_param_default();
        if param.is_null() {
            return Err("Unable to allocate Potrace parameters".to_string());
        }

        (*param).turdsize = 4;
        (*param).turnpolicy = POTRACE_TURNPOLICY_MINORITY;
        (*param).alphamax = 1.0;
        (*param).opticurve = 1;
        (*param).opttolerance = 0.2;

        let state = potrace_trace(param, bitmap.as_ptr());
        potrace_param_free(param);

        if state.is_null() {
            return Err("Potrace trace failed".to_string());
        }

        let result = if (*state).status == POTRACE_STATUS_OK {
            let paths = collect_paths((*state).plist);
            Ok(paths)
        } else {
            Err("Potrace trace incomplete".to_string())
        };

        potrace_state_free(state);
        result
    }
}

struct PotraceBitmapBuffer {
    bitmap: PotraceBitmap,
    words: Vec<c_ulong>,
}

impl PotraceBitmapBuffer {
    fn new(width: u32, height: u32) -> Result<Self, String> {
        let word_bits = c_ulong::BITS as u32;
        let dy = width.div_ceil(word_bits);
        let word_count = dy
            .checked_mul(height)
            .ok_or_else(|| "Bitmap is too large for Potrace".to_string())?;
        let mut words = vec![0 as c_ulong; word_count as usize];
        let bitmap = PotraceBitmap {
            w: width as c_int,
            h: height as c_int,
            dy: dy as c_int,
            map: words.as_mut_ptr(),
        };

        Ok(Self { bitmap, words })
    }

    fn set(&mut self, x: u32, y: u32) {
        let word_bits = c_ulong::BITS as u32;
        let word_index = (y * self.bitmap.dy as u32 + x / word_bits) as usize;
        let bit = word_bits - 1 - (x % word_bits);
        self.words[word_index] |= (1 as c_ulong) << bit;
    }

    fn as_ptr(&self) -> *const PotraceBitmap {
        &self.bitmap
    }
}

unsafe fn collect_paths(root: *mut PotracePath) -> Vec<String> {
    let mut result = Vec::new();
    let mut path = root;

    while !path.is_null() {
        let mut d = path_to_svg(&(*path).curve, true);
        let mut child = (*path).childlist;
        while !child.is_null() {
            d.push(' ');
            d.push_str(&path_to_svg(&(*child).curve, true));
            child = (*child).sibling;
        }

        if !d.is_empty() {
            result.push(d);
        }

        child = (*path).childlist;
        while !child.is_null() {
            result.extend(collect_paths((*child).childlist));
            child = (*child).sibling;
        }

        path = (*path).sibling;
    }

    result
}

unsafe fn path_to_svg(curve: *const PotraceCurve, absolute_start: bool) -> String {
    if curve.is_null() || (*curve).n <= 0 {
        return String::new();
    }

    let segment_count = (*curve).n as usize;
    let controls = std::slice::from_raw_parts((*curve).c, segment_count);
    let tags = std::slice::from_raw_parts((*curve).tag, segment_count);
    let start = controls[segment_count - 1][2];
    let mut parts = Vec::with_capacity(segment_count + 2);

    if absolute_start {
        parts.push(format!("M {},{}", fmt_f(start.x), fmt_f(start.y)));
    } else {
        parts.push(format!("m {},{}", fmt_f(start.x), fmt_f(start.y)));
    }

    for index in 0..segment_count {
        let points = controls[index];
        match tags[index] {
            POTRACE_CORNER => {
                parts.push(format!("L {},{}", fmt_f(points[1].x), fmt_f(points[1].y)));
                parts.push(format!("L {},{}", fmt_f(points[2].x), fmt_f(points[2].y)));
            }
            POTRACE_CURVETO => {
                parts.push(format!(
                    "C {},{} {},{} {},{}",
                    fmt_f(points[0].x),
                    fmt_f(points[0].y),
                    fmt_f(points[1].x),
                    fmt_f(points[1].y),
                    fmt_f(points[2].x),
                    fmt_f(points[2].y)
                ));
            }
            _ => {}
        }
    }

    parts.push("Z".to_string());
    parts.join(" ")
}

fn fmt_f(value: f64) -> String {
    let rounded = (value * 100.0).round() / 100.0;
    let mut text = format!("{rounded:.2}");
    while text.contains('.') && text.ends_with('0') {
        text.pop();
    }
    if text.ends_with('.') {
        text.pop();
    }
    if text == "-0" {
        "0".to_string()
    } else {
        text
    }
}

fn unique_pixels(pixels: &[[u8; 3]]) -> Vec<[u8; 3]> {
    let mut seen = HashSet::new();
    let mut unique = Vec::new();

    for pixel in pixels {
        let key = ((pixel[0] as u32) << 16) | ((pixel[1] as u32) << 8) | pixel[2] as u32;
        if seen.insert(key) {
            unique.push(*pixel);
        }
    }

    unique
}

fn initial_centroids(unique_pixels: &[[u8; 3]], cluster_count: usize) -> Vec<ColorF> {
    let mut centroids = vec![ColorF::from_rgb(unique_pixels[0])];

    while centroids.len() < cluster_count {
        let mut best_pixel = unique_pixels[0];
        let mut best_distance = -1.0_f32;

        for pixel in unique_pixels {
            let distance = centroids
                .iter()
                .map(|centroid| distance_to_centroid(*pixel, *centroid))
                .fold(f32::INFINITY, f32::min);

            if distance > best_distance {
                best_distance = distance;
                best_pixel = *pixel;
            }
        }

        if best_distance <= 0.0 {
            break;
        }

        centroids.push(ColorF::from_rgb(best_pixel));
    }

    centroids
}

fn nearest_centroid(pixel: [u8; 3], centroids: &[ColorF]) -> usize {
    let mut best_index = 0;
    let mut best_distance = f32::INFINITY;

    for (index, centroid) in centroids.iter().enumerate() {
        let distance = distance_to_centroid(pixel, *centroid);
        if distance < best_distance {
            best_distance = distance;
            best_index = index;
        }
    }

    best_index
}

fn distance_to_centroid(pixel: [u8; 3], centroid: ColorF) -> f32 {
    let dr = pixel[0] as f32 - centroid.r;
    let dg = pixel[1] as f32 - centroid.g;
    let db = pixel[2] as f32 - centroid.b;
    dr * dr + dg * dg + db * db
}

#[cfg(test)]
fn preview_label(
    image: &QuantizedImage,
    x: u32,
    _y: u32,
    preview_width: u32,
    _preview_height: u32,
    source_y: u32,
) -> usize {
    let source_x = ((x as u64 * image.width as u64) / preview_width as u64) as u32;
    let source_index = (source_y * image.width + source_x) as usize;
    image.labels[source_index]
}

fn should_skip_color(color: [u8; 3], exclude_white: bool, exclude_black: bool) -> bool {
    (exclude_white && is_white_like(color)) || (exclude_black && is_black_like(color))
}

fn is_white_like(color: [u8; 3]) -> bool {
    color[0] > 240 && color[1] > 240 && color[2] > 240
}

fn is_black_like(color: [u8; 3]) -> bool {
    color[0] < 15 && color[1] < 15 && color[2] < 15
}

fn rgb_to_hex(color: [u8; 3]) -> String {
    format!("#{:02x}{:02x}{:02x}", color[0], color[1], color[2])
}

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('"', "&quot;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn quantizes_fixture_image() {
        let fixture = fixture_path("flat_shapes.png");
        let bytes = std::fs::read(fixture).expect("fixture should be readable");
        let quantized = quantize_image_bytes(&bytes, 6, "light").expect("fixture should quantize");

        assert_eq!(quantized.width, 128);
        assert_eq!(quantized.height, 96);
        assert!(!quantized.palette.is_empty());
        assert!(quantized.palette.len() <= 6);
        assert_eq!(
            quantized.labels.len(),
            (quantized.width * quantized.height) as usize
        );
    }

    #[test]
    fn preview_svg_is_valid_shape_document() {
        let fixture = fixture_path("icon_marks.png");
        let bytes = std::fs::read(fixture).expect("fixture should be readable");
        let quantized = quantize_image_bytes(&bytes, 7, "light").expect("fixture should quantize");
        let svg = quantized_preview_svg(&quantized, "icon_marks.png", "light", false, true);

        assert!(svg.starts_with("<svg "));
        assert!(svg.ends_with("</svg>"));
        assert!(svg.contains("<rect "));
    }

    #[test]
    fn potrace_svg_contains_flat_paths() {
        let fixture = fixture_path("flat_shapes.png");
        let bytes = std::fs::read(fixture).expect("fixture should be readable");
        let quantized = quantize_image_bytes(&bytes, 6, "light").expect("fixture should quantize");
        let svg = potrace_svg(&quantized, "flat_shapes.png", "light", false, false)
            .expect("potrace should trace");

        assert!(svg.starts_with("<svg "));
        assert!(svg.ends_with("</svg>"));
        assert!(svg.contains("<path "));
        assert!(svg.contains("RasterSVG Potrace flat path output"));
    }

    #[test]
    fn aggressive_smoothing_preserves_output_shape() {
        let fixture = fixture_path("poster_gradient.png");
        let bytes = std::fs::read(fixture).expect("fixture should be readable");
        let quantized =
            quantize_image_bytes(&bytes, 8, "aggressive").expect("fixture should quantize");

        assert_eq!(quantized.width, 112);
        assert_eq!(quantized.height, 88);
        assert!(quantized.palette.len() <= 8);
        assert_eq!(
            quantized.labels.len(),
            (quantized.width * quantized.height) as usize
        );
    }

    fn fixture_path(name: &str) -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("tests")
            .join("fixtures")
            .join("baseline")
            .join(name)
    }
}
