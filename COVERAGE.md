# Screenpipe Coverage

Screenpipe tracks coverage at two complementary layers:

- Tauri/WebDriver E2E coverage: real product UX and local API behavior by platform.
- Core engine coverage: Rust behavioral flow coverage across capture, audio, DB, accessibility, and engine crates.

These dashboards are behavioral maps, not a replacement for line or branch coverage.
Use them to see which product risks are represented, then layer runtime job
results and `cargo llvm-cov` data on top when judging release confidence.

## Dashboards

- E2E dashboard: [apps/screenpipe-app-tauri/e2e/COVERAGE.md](apps/screenpipe-app-tauri/e2e/COVERAGE.md)
- Core engine dashboard: [docs/coverage/CORE.md](docs/coverage/CORE.md)

## Current Snapshot

### Tauri E2E

- Mapped specs: 81
- Declared test blocks: 238
- Weighted coverage points: 182.5

| Platform | Specs | Declared tests | Weighted points | Layers | Features | Critical score |
| --- | --- | --- | --- | --- | --- | --- |
| windows | 69 | 218 | 175.2 | 15 | 72 | 90% |
| macos | 77 | 201 | 153.3 | 17 | 73 | 88% |
| linux | 59 | 178 | 145.0 | 13 | 67 | 87% |

### Core Engine

- Mapped suites: 30
- Mapped Rust files: 297
- Active test blocks: 2788
- Ignored/manual test blocks: 133
- Weighted coverage points: 2298.7

| Platform | Suites | Active tests | Ignored tests | Weighted points | Layers | Flows | Critical score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| windows | 27 | 2661 | 128 | 2240.4 | 21 | 11 | 100% |
| macos | 27 | 2711 | 108 | 2249.9 | 22 | 11 | 100% |
| linux | 23 | 2355 | 102 | 1962.7 | 20 | 11 | 100% |

## Refresh

From `apps/screenpipe-app-tauri`:

```bash
bun run coverage:all
bun run coverage:all:check
```

For core line coverage, install/use `cargo llvm-cov` and feed its JSON
summary into `coverage:core`; the core dashboard documents the exact command.
