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

- Mapped specs: 102
- Declared test blocks: 287
- Weighted coverage points: 220.7

| Platform | Specs | Declared tests | Weighted points | Layers | Features | Critical score |
| --- | --- | --- | --- | --- | --- | --- |
| windows | 79 | 248 | 199.8 | 15 | 88 | 91% |
| macos | 98 | 250 | 191.5 | 17 | 90 | 90% |
| linux | 69 | 208 | 169.6 | 14 | 83 | 88% |

### Core Engine

- Mapped suites: 32
- Mapped Rust files: 313
- Active test blocks: 2954
- Ignored/manual test blocks: 134
- Weighted coverage points: 2427.0

| Platform | Suites | Active tests | Ignored tests | Weighted points | Layers | Flows | Critical score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| windows | 29 | 2823 | 129 | 2367.0 | 21 | 11 | 100% |
| macos | 29 | 2877 | 109 | 2378.1 | 22 | 11 | 100% |
| linux | 25 | 2512 | 102 | 2085.9 | 20 | 11 | 100% |

## Refresh

From `apps/screenpipe-app-tauri`:

```bash
bun run coverage:all
bun run coverage:all:check
```

For core line coverage, install/use `cargo llvm-cov` and feed its JSON
summary into `coverage:core`; the core dashboard documents the exact command.
