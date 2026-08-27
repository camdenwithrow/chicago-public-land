# Land to Homes Tracker

Land to Homes is a portfolio project for screening publicly owned Chicago parcels for transit-accessible housing potential. It will combine reproducible geospatial ingestion, an explainable scoring model, and an interactive parcel/site map.

The tracker is a research aid, not a determination that a site is legally, physically, environmentally, or financially ready for housing. See [todo.md](todo.md) for the methodology and delivery plan, [docs/data-sources.md](docs/data-sources.md) for source coverage and licensing decisions, and [docs/provenance.md](docs/provenance.md) for snapshot and freshness rules.

## Stack

- Python, GeoPandas, Shapely, and PyProj for ingestion and spatial analysis
- PostgreSQL/PostGIS for storage and spatial queries
- FastAPI for the HTTP API
- Semantic HTML, TypeScript, Tailwind CSS, and MapLibre GL JS for the web client
- Protomaps/PMTiles for the OpenStreetMap-derived basemap
- Socrata APIs and official transit sources for public data

## Local setup

Prerequisites:

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- Bun 1.3+
- Podman with a running Podman machine and Compose provider (required for PostGIS; not required for the scaffold tests)

```bash
cp .env.example .env
make install
make db-up
make dev-api
```

In a second terminal:

```bash
make dev-web
```

The API is available at `http://localhost:8000`, its OpenAPI docs at `http://localhost:8000/docs`, and the web app at `http://localhost:5173`.

Do not open `apps/web/index.html` directly with a `file://` URL. The browser cannot compile its TypeScript entry point or resolve Vite modules from a file origin; start the app with `make dev-web` and use the HTTP URL above.

The web app loads Vite variables from the repository-level `.env`. It chooses a basemap in this order:

1. `VITE_PROTOMAPS_API_KEY` uses the hosted Protomaps Style API.
2. `VITE_BASEMAP_URL` uses a local or hosted PMTiles archive.
3. With neither value, the map renders a neutral scaffold style.

Create a hosted API key in the Protomaps account portal and restrict its allowed origins before production deployment. The key is included in browser requests and must not be treated as a server-side secret. For a local archive, set `VITE_BASEMAP_URL` to an absolute HTTP URL such as `http://localhost:5173/maps/chicago.pmtiles`. Restart Vite after changing either value.

## Common commands

```bash
make install       # Resolve Python and web dependencies
make check         # Lint, type-check, and test everything
make test          # Run Python tests
make dev-api       # Run FastAPI with reload
make dev-web       # Run Vite
make db-up         # Start PostGIS
make db-down       # Stop local services
make ingest        # Pipeline entry point (scaffold)
make score         # Scoring entry point (scaffold)
uv run python -m pipeline sources  # Validate and summarize the source registry
```

## Repository layout

```text
apps/api/           FastAPI application
apps/web/           MapLibre web client
pipeline/           Ingestion and scoring commands
sql/                Database SQL and future migrations
tests/              Python tests
data/samples/       Small committed fixtures
docs/               Methodology and data-source documentation
infra/              Container definitions
```

## Data and secrets

Raw and processed data, PMTiles archives, credentials, and Socrata app tokens are intentionally ignored by Git. Small test fixtures under `data/samples/` may be committed when their license and provenance are documented.

Every future ingestion writes immutable raw bytes and a separate run manifest outside Git. The API's
`GET /meta` endpoint exposes source attribution and keeps publisher update dates distinct from tracker
processing dates.

## Podman on macOS

The database image is built locally from the multi-architecture PostgreSQL 16 Bookworm image with PostGIS installed from PostgreSQL's package repository. This avoids x86 emulation because the published `postgis/postgis` image does not provide an ARM64 manifest.

Initialize and start the Linux VM once:

```bash
podman machine init --now
```

For an existing stopped machine, use `podman machine start`. Confirm that Podman and its external Compose provider are ready:

```bash
podman info
podman compose version
```

Then run `make db-up`. To use Docker instead, override the engine for a command with `make CONTAINER_ENGINE=docker db-up`.
