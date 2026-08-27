# Provenance and snapshot policy

Every source fetch must be reproducible and independently dated. A daily tracker run does not imply
that a publisher updated its source that day.

## Run lifecycle

1. Resolve the source from `pipeline/sources.toml`.
2. Fetch and validate the response before any production table is replaced.
3. Validate required fields and adapter-owned field types with `SchemaContract`. Missing required
   fields or changed types raise `SchemaDriftError` and stop the source run.
4. Pass the original response bytes to `ProvenanceStore.record_response`.
5. The store writes one content-addressed snapshot beneath `data/raw/<source>/<hash-prefix>/`
   and one run manifest beneath `data/processed/provenance/runs/`.
6. Only after the snapshot and manifest exist may a future adapter publish normalized data.

Both data directories are ignored by Git. Production deployments should mount them on durable object
or filesystem storage with backups and retention controls; the repository contains no raw snapshots.

## Run manifest

Every fetch records:

- unique run ID;
- source key and human-readable source name;
- exact fetch or landing URL;
- publisher update time, when the publisher supplies one;
- timezone-aware fetch time;
- row count;
- SHA-256 checksum of the original response;
- pipeline/methodology version;
- immutable snapshot path.

Identical responses share a content-addressed snapshot but still create separate run manifests. This
preserves every fetch event without storing duplicate large responses. Snapshot files are created
exclusively and are never overwritten; a checksum conflict fails the run.

## Schema contracts

The registry's `expected_fields` are always required. Each source adapter must also provide canonical
publisher field types for fields whose type affects parsing. Additional publisher fields are allowed,
but a required-field removal or a contracted type change aborts ingestion with a detailed error.
Schema changes are reviewed and versioned before updating a contract.

## Application freshness

`GET /meta` combines the registry with the newest run manifest for each source. It returns attribution,
license, source URL, `source_updated_at`, and `fetched_at`, plus the most recent tracker processing time.
The web application displays publisher and tracker dates separately and says when either value is
unavailable. Static attribution remains visible even when the API is offline.

Configure a different manifest directory with `PROVENANCE_RUNS_DIR`. The raw snapshot root is supplied
to `ProvenanceStore` by the future ingestion runner so local, object-store-mounted, and test paths can
be isolated without changing source adapters.
