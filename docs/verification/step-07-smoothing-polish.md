# Step 7 Verification - Smoothing and Region Cleanup

## Implemented

- Added native smoothing modes in the Rust engine:
  - `light`: radius 1, conservative edge-aware averaging;
  - `aggressive`: radius 2, stronger edge-aware averaging.
- Added label polishing after K-Means to reduce isolated noisy pixels before
  tracing.
- Kept `excludeWhite` and `excludeBlack` filtering in the native conversion
  path.
- Added a Rust test that exercises aggressive smoothing on the baseline
  fixtures.

## How to Verify

Run:

```bash
/Users/ale/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml
```

Expected result:

- all Rust tests pass;
- `aggressive_smoothing_preserves_output_shape` is present in the output.

Optional visual check:

1. Start the Tauri app.
2. Open one of the fixture images in `tests/fixtures/baseline/`.
3. Convert once with `light` and once with `aggressive`.
4. The aggressive result should be smoother, with fewer tiny isolated regions.

## Verified Locally

Verified with:

```bash
/Users/ale/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml
```

Result:

- 4 tests passed after Step 8 added the Potrace test as well.
