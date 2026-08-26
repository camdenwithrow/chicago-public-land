# Land to Homes Tracker

Land to Homes is a portfolio project for screening publicly owned Chicago parcels for transit-accessible housing potential. It will combine reproducible geospatial ingestion, an explainable scoring model, and an interactive parcel/site map.

The tracker is a research aid, not a determination that a site is legally, physically, environmentally, or financially ready for housing. See [todo.md](todo.md) for the methodology and delivery plan.

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
- Docker with Compose (required for PostGIS; not required for the scaffold tests)

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

If `VITE_BASEMAP_URL` is unset, the map renders a neutral scaffold style. Set it to an absolute `.pmtiles` URL to exercise the Protomaps protocol integration. A complete styled basemap is part of the map UI milestone.

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
