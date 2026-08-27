# Reproducible ingestion

The Phase 2 pipeline implements a complete vertical slice for Chicago's City-Owned Land Inventory. The generic Socrata client contains transport concerns only; dataset field selection, schema expectations, and normalization live in the City-owned-land adapter. Every additional source must receive its own adapter at this boundary.

## Run it

Start PostGIS and run the published load:

```bash
make db-up
make ingest
```

To exercise fetching and validation without changing the database:

```bash
uv run python -m pipeline ingest --no-publish
```

The optional `--page-size` flag changes the Socrata page size. `SOCRATA_APP_TOKEN` is sent as an `X-App-Token` header when configured, but is never included in pipeline logs.

## Processing contract

Each run performs these steps in order:

1. Fetch Socrata metadata and verify required fields and source types.
2. Fetch only the adapter's required columns using stable record-ID ordering and deterministic pagination.
3. Save the exact response pages and a provenance manifest before attempting publication.
4. Normalize identifiers, names, dates, nulls, and geometry while preserving source IDs and original owner text.
5. Store source geometry in EPSG:4326 and transform analytical geometry to Illinois StatePlane East, EPSG:3435.
6. Write an immutable quality summary and any quarantined records.
7. Apply quality gates, stage valid rows, verify the staging count, and replace that source's published rows inside one database transaction.

The published table is `raw.public_land_inventory`. Its primary key is `(source_key, source_record_id)`. Re-running a release replaces the prior rows for that source rather than appending duplicates. A failed validation or database operation leaves the previously published release intact.

## Audit artifacts

Generated artifacts are intentionally ignored by Git:

```text
data/raw/<source>/<date>/<run>.*          Exact response snapshot
data/processed/provenance/runs/<run>.json Run manifest and checksum
data/processed/quality/<run>.json          Quality counts
data/processed/quarantine/<source>/*.jsonl Rejected source records
```

Quality summaries report rows read and written, missing IDs, missing geometry, invalid and repaired geometry, duplicates, unmatched joins, and changes from the previous source count. A zero-row response, an empty valid result, or a source-count change greater than `MAJOR_COUNT_CHANGE_THRESHOLD` (20% by default) blocks publication after audit artifacts are saved.

Missing coordinates are counted but do not reject City inventory records because the source contains valid parcel IDs without point coordinates; parcel geometry matching belongs to Phase 4. Malformed geometry is quarantined. Missing constraint data must continue to mean unknown rather than unconstrained.

## Configuration

The pipeline reads the repository `.env` file:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Local `land_to_homes` database | SQLAlchemy PostGIS connection |
| `SOCRATA_APP_TOKEN` | Empty | Optional Socrata application token |
| `RAW_DATA_DIR` | `data/raw` | Immutable response snapshots |
| `PROCESSED_DATA_DIR` | `data/processed` | Quality, quarantine, and provenance artifacts |
| `PIPELINE_VERSION` | `v1.0.0` | Version recorded on each run |
| `MAJOR_COUNT_CHANGE_THRESHOLD` | `0.20` | Absolute row-count change that blocks publication |

The current production adapter covers one source. The remaining registry entries are research candidates and must not be passed through the City adapter; each needs its own schema contract, normalization rules, fixtures, and quality review before it can publish.
