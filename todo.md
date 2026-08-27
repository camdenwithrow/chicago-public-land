# Land to Homes Tracker — Implementation Plan

Identify publicly owned Chicago parcels with strong potential for transit-accessible housing development. The first release should be an explainable screening tool: it helps users find and compare promising parcels, but it does not claim that a parcel is legally, environmentally, or financially ready for development.

## MVP definition

The MVP is complete when a user can:

- [ ] Open a Chicago map and see publicly owned parcels colored by development-potential score.
- [ ] Pan and zoom without downloading the full parcel dataset.
- [ ] Filter parcels by owner, score, parcel area, transit distance, zoning, and community area.
- [ ] Select a parcel and see its source attributes, score components, nearby transit, known constraints, and data freshness.
- [ ] Open the original public-data record used for the parcel when the source provides a stable URL.
- [ ] Download the current filtered result set as GeoJSON or CSV.
- [ ] Re-run the data pipeline reproducibly and publish a new dated dataset release.

## Agreed product decisions

- [x] Treat an individual tax parcel/PIN as the canonical parcel and also create assembled sites from contiguous parcels with compatible public ownership. Let users switch between both map layers.
- [x] Include parcels geographically within Chicago that are owned by Illinois, Cook County, the City of Chicago, or their non-federal public agencies and special-purpose units (for example, CTA, CHA, CPS, and park districts). Exclude federally owned land.
- [x] Build this as a polished portfolio project. Optimize for an understandable public demo, reproducible engineering, and clear technical documentation rather than an agency-specific approval workflow.
- [x] Run the update pipeline daily. Show both `source updated at` and `tracker processed at` so a daily run does not imply that every source publishes daily.
- [x] Show both individual parcels and assembled sites; neither representation should hide the other.
- [x] Treat confirmed legal or physical unviability as a hard exclusion. Keep active/in-use public land visible for completeness, but flag it and cap its score so it cannot appear as a strong candidate.
- [x] Start methodology versioning at `v1.0.0` and change the version whenever weights, thresholds, exclusions, or source interpretations change.

## Methodology v1.0.0

### Scope and unit of analysis

- The project area is the City of Chicago boundary.
- Public ownership includes State of Illinois, Cook County, City of Chicago, and non-federal public authorities, districts, departments, and agencies that own land within the project area.
- Federal ownership is out of scope, even when a federal parcel lies within Chicago.
- A **parcel** is an individual tax parcel/PIN matched to an authoritative public-land record.
- A **site** is a derived group of contiguous or near-contiguous parcels with compatible public ownership. Streets, rail rights-of-way, incompatible ownership, or other barriers must prevent inappropriate grouping.
- Every site must retain links to its component parcels and original source records.

### Meaning of housing potential

Housing potential is a screening score based on several independently visible factors:

1. **Viability and constraints:** known environmental conditions, flood or wetland concerns, protected use, deed or disposition restrictions, rights-of-way, utilities, parcel access, and other physical or legal barriers.
2. **Current use/readiness:** vacant or underused land ranks above an active public facility or otherwise developed, in-use land.
3. **Transit and residential context:** access to rail or frequent bus service and proximity to existing residential areas.
4. **Physical developability:** usable area, shape, contiguity, frontage/access, and other site characteristics.
5. **Zoning and policy context:** existing residential or mixed-use permission, overlays, and approvals likely to be required.

The score is not a determination that housing can or should be built. It is a reproducible way to prioritize further research.

### Transit-accessible definition

- Prefer walking-network distance to CTA rail stations and frequent bus stops when reliable network and service-frequency data are available.
- The first vertical slice may use straight-line distance, but the UI must label it as approximate.
- Keep rail distance, bus distance, route/service information, and the combined transit component separately visible.

### Exclusions, low scores, and uncertainty

- Hard-exclude a parcel only when an authoritative source confirms a severe legal or physical constraint that makes housing development unviable under the methodology.
- Mark active/in-use public land with an `active_public_use` flag and cap its total score at 20/100. Do not silently remove it.
- Treat parks, active schools, rights-of-way, utility land, and active civic facilities as in-use unless authoritative data supports a different status.
- Use penalties and warnings for potentially remediable environmental or regulatory issues; do not equate a hazard flag with permanent unbuildability.
- Treat missing constraint data as **unknown**, not as evidence that no constraint exists.
- Publish a separate data-confidence/coverage indicator so a high potential score with sparse evidence is visibly less certain.
- Preserve the source, observation date, rule, and score effect for every flag, cap, penalty, and exclusion.

## Proposed architecture

```text
Chicago/Cook County open data      CTA transit data
             |                           |
             +--- Python ingestion ------+
                         |
              raw snapshots + metadata
                         |
                GeoPandas validation
                         |
                    PostGIS
         raw -> staging -> core -> analytics
                         |
                      FastAPI
                 /parcels /sites /meta
                         |
              MapLibre web application
                         |
          Protomaps/PMTiles OSM basemap
```

Recommended repository layout:

```text
apps/
  api/                 # FastAPI application
  web/                 # MapLibre client
pipeline/              # Python ingestion, cleaning, joins, and scoring
sql/                   # PostGIS schema, views, indexes, and migrations
tests/                 # Pipeline, spatial, API, and end-to-end tests
data/
  samples/             # Small, redistributable test fixtures only
docs/                  # Methodology, data dictionary, and operations notes
infra/                 # Docker and deployment configuration
```

## Phase 0 — Project foundation

- [x] Add a `README.md` with the problem statement, local setup, architecture, and limitations.
- [x] Choose package tooling and pin versions (`uv` for Python and Bun for the HTML/TypeScript/Tailwind web app).
- [x] Add Python dependencies: FastAPI, Uvicorn, GeoPandas, Shapely, PyProj, SQLAlchemy, GeoAlchemy2, Alembic, psycopg, httpx, Pydantic, and tenacity.
- [x] Add web dependencies: TypeScript, Tailwind CSS, MapLibre GL JS, PMTiles, and Protomaps base themes.
- [x] Create a local Compose stack for PostGIS, the API, and the web app, using Podman by default.
- [x] Add `.env.example`; keep Socrata app tokens and database credentials out of Git.
- [x] Add formatting, linting, type checking, and tests to CI.
- [x] Add common developer commands such as `make db-up`, `make ingest`, `make score`, `make test`, and development servers.
- [x] Add a synthetic Chicago-area fixture so tests do not depend on live APIs.

## Phase 1 — Data-source inventory and provenance

Do not hard-code a dataset identifier until its publisher, fields, update cadence, license, and geometry quality have been checked. Put the final choices in `docs/data-sources.md`.

### Required MVP sources

- [x] Find authoritative inventories for City of Chicago, Cook County, State of Illinois, and relevant non-federal public-agency land within Chicago; record gaps where no reliable inventory exists.
- [x] Add an explicit federal-owner classification so federal parcels are excluded deterministically rather than by an informal name filter.
- [x] Find authoritative parcel/PIN geometry and ownership attributes; determine whether the geometry comes from the City of Chicago or Cook County and whether its terms allow redistribution.
- [x] Find Chicago zoning district polygons and any relevant planned-development or overlay boundaries.
- [x] Obtain official CTA transit stops and routes; use GTFS if it is the best authoritative source.
- [x] Find community area boundaries for navigation and summaries.
- [x] Identify records that mark parks, schools, libraries, police/fire facilities, rights-of-way, and other active public uses.
- [x] Use a Protomaps OpenStreetMap extract only for the basemap unless OSM-derived analytical fields are separately documented.

### Useful second-release sources

- [ ] Frequent-transit service or scheduled trip frequency, not just stop presence.
- [ ] Building footprints and current land use.
- [ ] Flood risk, wetlands, brownfields/environmental records, and landmark districts.
- [ ] Affordable-housing policy areas and relevant planning overlays.
- [ ] Assessed value, sale history, or other cost proxies, with clear caveats.
- [ ] Utilities or infrastructure capacity where publishable data exists.

### Provenance requirements

- [x] Create a source registry containing publisher, dataset ID/URL, license, fetch method, expected schema, update frequency, and contact information.
- [ ] Store every ingestion run with `source_name`, `source_url`, `source_updated_at`, `fetched_at`, row count, response checksum, and pipeline version.
- [ ] Save immutable raw responses or normalized GeoParquet snapshots outside Git.
- [ ] Add schema-drift checks that fail loudly when required fields disappear or change type.
- [ ] Make attribution and data-current dates visible in the application.

## Phase 2 — Reproducible ingestion

- [ ] Implement a reusable Socrata client with:
  - App-token support.
  - Pagination and deterministic ordering.
  - Configurable `$select`, `$where`, and incremental-update queries.
  - Retry/backoff for rate limits and transient failures.
  - Response and schema logging without leaking credentials.
- [ ] Build one source adapter per dataset rather than embedding dataset-specific rules in the generic client.
- [ ] Fetch only required columns for routine updates; retain a raw snapshot for auditability.
- [ ] Normalize column names, identifiers, dates, booleans, owner names, and null values.
- [ ] Preserve the original source record ID and original owner text.
- [ ] Convert geometry safely from source formats such as WKT, GeoJSON, latitude/longitude, or multipolygon fields.
- [ ] Validate geometry type, repair recoverable invalid polygons, and quarantine records that cannot be repaired.
- [ ] Standardize source geometry to EPSG:4326 on ingestion, then transform analytical geometry to EPSG:3435 for Chicago-area distance and area calculations.
- [ ] Load into PostGIS through staging tables inside a transaction; swap/publish only after validation passes.
- [ ] Make ingestion idempotent so rerunning the same source release does not duplicate records.
- [ ] Add data-quality summaries: rows read/written, missing IDs, invalid geometry, duplicates, unmatched joins, and major count changes.

## Phase 3 — PostGIS data model

- [ ] Set up Alembic migrations and enable PostGIS.
- [ ] Use database schemas to separate concerns:
  - `raw`: minimally changed source records.
  - `staging`: cleaned and normalized records for the current run.
  - `core`: stable parcels, owners, transit features, zoning, and boundaries.
  - `analytics`: derived sites, metrics, scores, and materialized views.
- [ ] Create core tables similar to:

```text
core.parcel
  id, pin, source_record_id, owner_id, address, status,
  area_sqft, geom_3435, geom_4326, source_run_id, updated_at

core.owner
  id, canonical_name, owner_class, agency_level, original_names

core.transit_stop
  id, agency, mode, name, route_ids, geom_3435, service_date

core.zoning_area
  id, zoning_class, attributes, geom_3435, source_run_id

analytics.parcel_metric
  parcel_id, score_version, metrics_json, constraints_json,
  component_scores_json, total_score, calculated_at

analytics.site
  id, owner_class, parcel_count, area_sqft, geom_3435, score
```

- [ ] Decide whether `geom_4326` is stored or exposed as a transformed view; avoid two uncontrolled canonical geometries.
- [ ] Add GiST spatial indexes and B-tree indexes for owner, score, area, zoning, community area, and update date.
- [ ] Enforce geometry type/SRID, unique source IDs, valid score ranges, and foreign keys.
- [ ] Create a parcel lineage table for merges, splits, and assembled sites.
- [ ] Create materialized views for map display and summary statistics; refresh them only after a successful pipeline run.

## Phase 4 — Parcel matching and site assembly

- [ ] Establish a deterministic parcel identity strategy using source record ID and PIN where available.
- [ ] Join public-land inventory records to parcel geometry using, in order: exact PIN, normalized source key, and carefully reviewed spatial matching.
- [ ] Produce an “unmatched records” report rather than silently dropping records.
- [ ] Normalize owner names into explicit agency classes while preserving original values.
- [ ] Flag ownership conflicts between datasets for review.
- [ ] Calculate parcel area, perimeter, compactness, centroid/point-on-surface, and approximate frontage when supportable.
- [ ] Flag unusually small, narrow, or irregular parcels; keep thresholds configurable.
- [ ] Build an optional site-assembly step that groups touching/near-touching parcels with compatible ownership and excludes separation by streets or rail rights-of-way.
- [ ] Preserve parcel-to-site membership so the UI can explain every assembled site.
- [ ] Manually review a stratified sample across owners, sizes, and community areas before publishing.

## Phase 5 — Explainable scoring model

Start with a transparent rule-based score. Keep raw metrics separate from score weights so the policy can change without re-ingesting data.

### Candidate v1 score (0–100)

This weighting intentionally makes practical viability and current use more important than proximity alone.

- [ ] Viability and known constraints — 0–30 points
  - Environmental, physical, legal, access, public-use, deed, and disposition constraints.
  - Severe confirmed unviability is an exclusion; remediable or uncertain issues receive an explainable warning or penalty.
- [ ] Current-use readiness — 0–25 points
  - Vacant or underused land receives more credit than developed, active, or operational public land.
  - Apply the 20/100 total-score cap when `active_public_use` is confirmed.
- [ ] Transit and residential context — 0–20 points
  - Walking-network distance to rail and frequent bus service, when available.
  - Proximity to existing residential areas as context for potential housing use.
- [ ] Physical developability — 0–15 points
  - Usable land area, compactness, contiguity, frontage/access proxy, and parcel assembly potential.
  - Avoid treating “larger is always better”; use documented bands.
- [ ] Zoning/policy capacity — 0–10 points
  - Existing residential/mixed-use allowance and relevant overlays.
  - Clearly label assumptions that require rezoning, disposition, or planned-development review.

### Scoring implementation

- [ ] Put thresholds and weights in a versioned YAML/TOML configuration file.
- [ ] Store raw values, normalized component scores, penalties, exclusions, and total score for every parcel/site.
- [ ] Calculate a separate confidence/coverage indicator from source recency, match quality, and metric completeness; do not blend it into the potential score.
- [ ] Use straight-line transit distance for the first working slice only; replace it with walking-network distance or clearly label it as approximate.
- [ ] Distinguish hard exclusions from soft penalties; excluded sites should not merely receive a low score.
- [ ] Enforce and test the `active_public_use` score cap of 20/100.
- [ ] Do not include protected-class demographics in parcel ranking.
- [ ] Test threshold boundary values and missing-data behavior.
- [ ] Add sensitivity analysis showing how rankings change under plausible weight changes.
- [ ] Review the top results and random middle/low-score samples with domain experts.
- [ ] Publish the complete scoring methodology and score version in the UI.

## Phase 6 — FastAPI service

- [ ] Create settings, database pooling, structured logs, error handling, and health endpoints.
- [ ] Define Pydantic response models and publish useful OpenAPI descriptions.
- [ ] Implement MVP endpoints:
  - `GET /health` — process and database health.
  - `GET /api/v1/meta` — releases, source dates, methodology version, and filter options.
  - `GET /api/v1/parcels` — viewport query plus filters, sorting, pagination, and compact GeoJSON.
  - `GET /api/v1/parcels/{id}` — full parcel facts, score explanation, constraints, and source lineage.
  - `GET /api/v1/sites` and `GET /api/v1/sites/{id}` — assembled-site equivalents when enabled.
  - `GET /api/v1/summary` — counts and score/area summaries for the current filters.
  - `GET /api/v1/export` — bounded CSV or GeoJSON export.
- [ ] Require a bounding box and zoom/limit for geometry list endpoints.
- [ ] Return simplified geometry appropriate to zoom; keep full geometry for details/export.
- [ ] Validate bounding boxes, filter values, sort fields, and maximum export size.
- [ ] Use parameterized SQL and statement timeouts.
- [ ] Add ETags/cache headers keyed by dataset release and query.
- [ ] Add CORS restrictions and basic rate limiting for a public deployment.
- [ ] Measure query plans against the full expected dataset and add indexes where justified.
- [ ] Consider vector tiles (`MVT`) from PostGIS only if filtered GeoJSON is not fast enough for the MVP.

## Phase 7 — MapLibre + Protomaps web app

- [ ] Create an accessible responsive shell with map, filters, results, legend, methodology, and about/data-source views.
- [ ] Configure MapLibre with a Protomaps/PMTiles OpenStreetMap basemap and required attribution.
- [ ] Use a Chicago default extent and preserve map/filter state in the URL.
- [ ] Add a prominent parcel/site layer switch and preserve the selected representation in the URL.
- [ ] Load parcel data by viewport and debounce requests while the map moves.
- [ ] Style parcels with a color-blind-safe score ramp and a distinct excluded/unknown style.
- [ ] Add hover/focus highlights and a selected-parcel outline.
- [ ] Build a detail drawer showing:
  - Address/PIN and public owner.
  - Total and component scores.
  - Parcel/site area and zoning.
  - Transit distances and nearby routes/stops.
  - Known constraints and missing data.
  - Source links, data dates, and methodology version.
- [ ] Add filters for minimum score, owner/agency, parcel area, transit distance, zoning, community area, and exclusion status.
- [ ] Add a sortable table/list synchronized with the map.
- [ ] Add a clear legend and explanation of why a site received its score.
- [ ] Add empty, loading, stale-data, API-error, and offline-basemap states.
- [ ] Make keyboard navigation, focus order, contrast, and screen-reader labels part of the MVP acceptance test.
- [ ] Avoid exposing private Protomaps credentials in the client; use a public asset URL or appropriately scoped token.

## Phase 8 — Quality, validation, and trust

### Automated tests

- [ ] Unit-test normalization, owner classification, geometry repair, thresholds, exclusions, and score calculations.
- [ ] Contract-test every source adapter against saved fixtures.
- [ ] Add spatial tests for SRIDs, valid geometry, area ranges, point-in-polygon joins, nearest transit, and site assembly.
- [ ] Add database migration and API integration tests against PostGIS.
- [ ] Add endpoint tests for invalid filters, bounds, limits, empty results, and stable response schemas.
- [ ] Add browser tests for map loading, filters, parcel selection, URL state, and detail display.
- [ ] Add performance tests for representative low-, medium-, and high-density viewports.

### Data acceptance checks

- [ ] All published public-land records have a source record and ingestion run.
- [ ] No published geometry is empty, invalid, or assigned the wrong SRID.
- [ ] Total/component scores stay within documented ranges.
- [ ] Join, exclusion, missing-value, and owner-conflict rates stay below documented thresholds.
- [ ] Large changes in record count, public acreage, or score distribution require review before release.
- [ ] Compare a sample of parcels against the source portals and recent aerial/street context.
- [ ] Have a Chicago land-use/housing expert review false positives and false negatives.

## Phase 9 — Deployment and operations

- [ ] Choose hosting for PostGIS, API, static web assets, raw snapshots, and PMTiles.
- [ ] Build small production images and run migrations as an explicit release step.
- [ ] Serve the web app and basemap assets through a CDN with compression and range-request support for PMTiles.
- [ ] Schedule ingestion and scoring daily; skip unnecessary rebuilds when sources have not changed and publish only when validations pass.
- [ ] Keep the prior materialized views/release available for rollback.
- [ ] Back up PostGIS and test a restore.
- [ ] Add monitoring for API errors/latency, database capacity, failed ingestion, stale data, and basemap availability.
- [ ] Add a visible issue-reporting path for incorrect ownership or parcel facts.
- [ ] Document incident response, source outages, credential rotation, and manual republishing.
- [ ] Publish license, attribution, methodology, changelog, and privacy/accessibility statements.

## Suggested delivery milestones

### Milestone 1 — One vertical slice

- [ ] Ingest one public-land dataset and one authoritative transit-stop dataset.
- [ ] Load cleaned parcel polygons and stops into PostGIS.
- [ ] Calculate parcel area and nearest-stop distance.
- [ ] Serve one bounded parcel endpoint.
- [ ] Render and select parcels on a MapLibre/Protomaps map.

### Milestone 2 — Trustworthy MVP data

- [ ] Add authoritative parcel matching, owner normalization, zoning, community areas, exclusions, and data-quality reports.
- [ ] Review unmatched and conflicted records.
- [ ] Version and validate the first complete score.

### Milestone 3 — Usable MVP

- [ ] Finish filters, details, score explanations, summaries, exports, accessibility, and responsive behavior.
- [ ] Meet agreed API and map performance budgets.
- [ ] Publish methodology and source provenance.

### Milestone 4 — Production release

- [ ] Automate tested data releases and deployment.
- [ ] Add monitoring, backups, rollback, and user feedback.
- [ ] Complete expert review and resolve launch-blocking false positives.

## Early risks to track

- [ ] Public-land inventories may be incomplete, stale, or use records that do not align cleanly with tax parcels.
- [ ] Public ownership does not imply availability for housing or authority to dispose of a site.
- [ ] Straight-line transit proximity can overstate access across expressways, rail yards, rivers, or disconnected street networks.
- [ ] Zoning alone does not establish achievable unit count; planned developments, overlays, parking, setbacks, and review processes matter.
- [ ] Environmental and active-public-use data may be incomplete, so absence of a flag is not proof of absence.
- [ ] Parcel rankings can encode policy choices; weights, exclusions, missing data, and uncertainty must remain visible.
- [ ] OSM/Protomaps data and public datasets have separate licenses and attribution requirements.

## Post-MVP ideas

- [ ] Walking-network transit accessibility and frequency-weighted access.
- [ ] User-adjustable score weights with a shareable scenario URL.
- [ ] Side-by-side parcel/site comparison.
- [ ] Capacity scenarios with explicit zoning and affordability assumptions.
- [ ] Change history showing acquisitions, dispositions, ownership changes, and score movement.
- [ ] Public comments or annotations with moderation and audit history.
- [ ] Vector-tile delivery for larger regional datasets.
- [ ] A documented public API and downloadable versioned data releases.

## Definition of done for every data release

- [ ] Source snapshots and metadata are retained.
- [ ] Pipeline and migration tests pass.
- [ ] Data-quality thresholds pass or exceptions are documented and approved.
- [ ] Score version, source dates, record counts, and distribution changes are recorded.
- [ ] A human reviews top-ranked sites, a random sample, and all severe constraint/ownership conflicts.
- [ ] API and UI smoke tests pass against the candidate release.
- [ ] Attribution, methodology, and changelog are current.
- [ ] The previous release remains recoverable.
