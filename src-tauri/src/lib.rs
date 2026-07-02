mod engine;

use base64::Engine;
use serde::Serialize;
use std::path::Path;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct OpenImageResult {
    filename: String,
    data: String,
    path: String,
}

#[derive(Serialize)]
struct ConvertResult {
    svg: String,
    palette: Vec<String>,
}

#[tauri::command]
fn read_image_file(path: String) -> Result<OpenImageResult, String> {
    let bytes = std::fs::read(&path).map_err(|err| err.to_string())?;
    let filename = Path::new(&path)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("image")
        .to_string();

    Ok(OpenImageResult {
        filename,
        data: base64::engine::general_purpose::STANDARD.encode(bytes),
        path,
    })
}

#[tauri::command]
fn save_svg_file(path: String, content: String) -> Result<(), String> {
    std::fs::write(path, content).map_err(|err| err.to_string())
}

#[tauri::command]
fn close_app(window: tauri::WebviewWindow) -> Result<(), String> {
    window.close().map_err(|err| err.to_string())
}

#[tauri::command]
fn convert_image_placeholder(
    file_name: String,
    colors: u8,
    smoothing: String,
    exclude_white: bool,
    exclude_black: bool,
) -> ConvertResult {
    let palette = placeholder_palette(colors, exclude_white, exclude_black);
    let svg = placeholder_svg(&palette, &file_name, &smoothing);

    ConvertResult { svg, palette }
}

#[tauri::command]
fn convert_image_quantized(
    path: String,
    colors: u8,
    smoothing: String,
    exclude_white: bool,
    exclude_black: bool,
) -> Result<ConvertResult, String> {
    let bytes = std::fs::read(&path).map_err(|err| err.to_string())?;
    let source_name = Path::new(&path)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("image");
    let quantized = engine::quantize_image_bytes(&bytes, colors, &smoothing)?;
    let palette = engine::palette_to_hex(&quantized.palette);
    let svg = engine::potrace_svg(
        &quantized,
        source_name,
        &smoothing,
        exclude_white,
        exclude_black,
    )?;

    Ok(ConvertResult { svg, palette })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            read_image_file,
            save_svg_file,
            close_app,
            convert_image_placeholder,
            convert_image_quantized
        ])
        .run(tauri::generate_context!())
        .expect("error while running RasterSVG");
}

fn placeholder_palette(colors: u8, exclude_white: bool, exclude_black: bool) -> Vec<String> {
    let requested = colors.clamp(1, 30) as usize;
    let mut palette = vec![
        "#f8fafc".to_string(),
        "#111827".to_string(),
        "#3b82f6".to_string(),
        "#ef4444".to_string(),
        "#22c55e".to_string(),
        "#f59e0b".to_string(),
        "#14b8a6".to_string(),
        "#8b5cf6".to_string(),
    ];

    while palette.len() < requested {
        let index = palette.len() as u8;
        palette.push(format!(
            "#{:02x}{:02x}{:02x}",
            64_u8.wrapping_add(index.wrapping_mul(37)),
            96_u8.wrapping_add(index.wrapping_mul(53)),
            144_u8.wrapping_add(index.wrapping_mul(71))
        ));
    }

    palette.truncate(requested);

    let mut filtered = palette
        .into_iter()
        .filter(|color| !(exclude_white && is_white_like(color)))
        .filter(|color| !(exclude_black && is_black_like(color)))
        .collect::<Vec<_>>();

    if filtered.is_empty() {
        filtered.push("#3b82f6".to_string());
    }

    filtered
}

fn placeholder_svg(palette: &[String], file_name: &str, smoothing: &str) -> String {
    let safe_palette = if palette.is_empty() {
        vec!["#3b82f6".to_string()]
    } else {
        palette.to_vec()
    };

    let mut parts = vec![
        r#"<svg width="800" height="600" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">"#
            .to_string(),
        format!(
            r#"<!-- RasterSVG Tauri placeholder; source="{}"; smoothing="{}" -->"#,
            escape_xml(file_name),
            escape_xml(smoothing)
        ),
    ];

    parts.push(format!(
        r#"<rect x="0" y="0" width="800" height="600" fill="{}" />"#,
        safe_palette[0]
    ));

    for (index, color) in safe_palette.iter().enumerate().skip(1) {
        let x = 80 + (index as i32 * 58) % 560;
        let y = 86 + (index as i32 * 79) % 360;
        let w = 180 - (index as i32 * 7) % 70;
        let h = 120 + (index as i32 * 11) % 100;
        let rx = 8 + (index as i32 % 5) * 4;

        parts.push(format!(
            r#"<path d="M {x},{y} h {w} a {rx},{rx} 0 0 1 {rx},{rx} v {h} a {rx},{rx} 0 0 1 -{rx},{rx} h -{w} a {rx},{rx} 0 0 1 -{rx},-{rx} v -{h} a {rx},{rx} 0 0 1 {rx},-{rx} Z" fill="{color}" stroke="none" shape-rendering="crispEdges" />"#
        ));
    }

    parts.push(r##"<path d="M 116,438 C 214,356 320,496 424,394 C 518,302 612,392 700,318 L 700,510 L 116,510 Z" fill="#0f172a" opacity="0.22" stroke="none" />"##.to_string());
    parts.push("</svg>".to_string());
    parts.join("")
}

fn is_white_like(color: &str) -> bool {
    color.eq_ignore_ascii_case("#ffffff") || color.eq_ignore_ascii_case("#f8fafc")
}

fn is_black_like(color: &str) -> bool {
    color.eq_ignore_ascii_case("#000000") || color.eq_ignore_ascii_case("#111827")
}

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('"', "&quot;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}
