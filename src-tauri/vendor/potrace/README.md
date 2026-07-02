# Potrace 1.16

This directory contains the minimal Potrace 1.16 core library files required by
RasterSVG's native tracing backend.

Source: https://potrace.sourceforge.net/

Potrace is Copyright (C) 2001-2019 Peter Selinger and is distributed under the
GNU General Public License. See `COPYING`.

Only the core `potracelib` files are vendored here. Command-line frontends and
format-specific backends are intentionally excluded; RasterSVG generates its own
layered SVG output from the Potrace curve API.
