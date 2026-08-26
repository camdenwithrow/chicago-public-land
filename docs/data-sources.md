# Data source registry

No production source is approved yet. Add a source only after confirming its publisher, dataset identifier, stable URL, license, geometry/field quality, update cadence, and redistribution terms.

| Source | Publisher | Dataset ID/URL | License | Update cadence | Required fields | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Public land inventory | TBD | TBD | TBD | TBD | source ID, owner, status, PIN/address, geometry or join key | Research |
| Parcel geometry | TBD | TBD | TBD | TBD | PIN, polygon, source update time | Research |
| Zoning | TBD | TBD | TBD | TBD | zoning class, polygon | Research |
| CTA transit | TBD | TBD | TBD | TBD | stops, routes, service | Research |
| Community areas | TBD | TBD | TBD | TBD | area number/name, polygon | Research |

Every ingestion run must retain the source URL, source update time, fetch time, row count, checksum, and pipeline version.

