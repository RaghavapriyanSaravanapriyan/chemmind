# Repository Test Suite

This folder is the root entry point for the existing AI tests and frontend surface checks.

## Run the root suite

From the repository root:

```bash
python -m pytest tests
```

The wrapper modules collect the existing suites from `ai/tests`; the original test files remain in their package directories. The backend is implemented in Rust and its tests are compiled and run separately:

```bash
cargo test --manifest-path backend_rust/Cargo.toml
```

Frontend source/API contract checks are included in `test_frontend_contracts.py`. A browser test runner is not configured yet, so these checks do not replace real click-through tests for rendered components.
