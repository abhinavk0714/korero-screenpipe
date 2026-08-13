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

- Mapped specs: 113
- Declared test blocks: 322
- Weighted coverage points: 254.0

| Platform | Specs | Declared tests | Weighted points | Layers | Features | Critical score |
| --- | --- | --- | --- | --- | --- | --- |
| windows | 87 | 280 | 230.6 | 16 | 91 | 92% |
| macos | 109 | 285 | 224.8 | 17 | 94 | 90% |
| linux | 76 | 237 | 199.2 | 15 | 86 | 88% |

### Core Engine

- Mapped suites: 32
- Mapped Rust files: 321
- Active test blocks: 3071
- Ignored/manual test blocks: 137
- Weighted coverage points: 2528.1

| Platform | Suites | Active tests | Ignored tests | Weighted points | Layers | Flows | Critical score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| windows | 29 | 2940 | 132 | 2468.1 | 21 | 11 | 100% |
| macos | 29 | 2993 | 112 | 2478.5 | 22 | 11 | 100% |
| linux | 25 | 2626 | 105 | 2184.9 | 20 | 11 | 100% |

## Refresh

From `apps/screenpipe-app-tauri`:

```bash
bun run coverage:all
bun run coverage:all:check
```

For core line coverage, install/use `cargo llvm-cov` and feed its JSON
summary into `coverage:core`; the core dashboard documents the exact command.
