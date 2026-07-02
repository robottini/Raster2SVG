# Notices

## Potrace and potracer

RasterSVG uses Potrace-compatible tracing in two places:

- the legacy Python backend uses `potracer`, a Python port of Potrace, through
  `backend/main.py`;
- the native Tauri/Rust app vendors the minimal Potrace 1.16 core under
  `src-tauri/vendor/potrace/` and links it into the desktop application.

Potrace is authored by Peter Selinger and converts bitmaps into vector
graphics. The official Potrace site states that Potrace is licensed under the
GNU General Public License, version 2 or, at the user's option, any later
version:

https://potrace.sourceforge.net/

The installed Python package metadata for `potracer` also declares GPLv2+.
The vendored Potrace source includes its upstream `COPYING` file.

## Trademark note

"Potrace" is a trademark of Peter Selinger. This project should describe its
use accurately as an integration or compatible tracing backend, and should not
rename itself in a way that implies it is the official Potrace project.

## Native tracing note

The Tauri/Rust implementation keeps this licensing constraint in mind. Because
the native app vendors and links Potrace code, the distributed application
remains under a GPL-compatible license and includes the corresponding source
and notices.
