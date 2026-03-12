# Contributing to pinchsms

## Setup

```bash
git clone https://github.com/openclaw/pinchsms
cd pinchsms
uv sync --all-extras --group dev
```

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Run checks:

```bash
uv run ruff check --fix && uv run ruff format
uv run ty check
uv run pytest -q --cov=pinchsms
```

4. Open a PR against `main`

## Adding Modem Support

See [docs/adding-modems.md](docs/adding-modems.md) for a step-by-step guide.

## Code Style

- Linting and formatting with ruff
- Type checking with ty
- Protocols over ABCs
- stdlib over third-party when reasonable
- Tests mirror `src/` structure in `tests/`

## Pull Requests

- One logical change per PR
- Tests required for new functionality
- All checks must pass
