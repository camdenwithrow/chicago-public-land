# Data sources and coverage

Registry version **1.1.0**, reviewed **August 27, 2026**. The machine-readable configuration is
[`pipeline/sources.toml`](../pipeline/sources.toml). A source marked selected can support the MVP;
provisional sources need a licensing or technical question resolved before public release.

The tracker checks every source daily, but it does not imply that publishers update their data
daily. Each ingestion will retain both the publisher's `source_updated_at` and our `fetched_at`.

## MVP source decisions

| Role | Source | ID/service | Decision | Key caution |
| --- | --- | --- | --- | --- |
| City ownership | [City-Owned Land Inventory](https://data.cityofchicago.org/d/aksk-kvfp) | `aksk-kvfp` | Selected | Not a complete inventory of every public agency and not proof of clear title. |
| Parcel polygons | [CookViewer Current Parcel](https://gis.cookcountyil.gov/traditional/rest/services/cookVwrDynmc/MapServer/44) | `MapServer/44` | Provisional | Official current polygons, but redistribution permission is not stated. |
| Parcel context | [Parcel Universe (Current Year Only)](https://datacatalog.cookcountyil.gov/d/pabr-t5kh) | `pabr-t5kh` | Provisional | Centroids and attributes, not polygon geometry; catalog license is unspecified. |
| Ownership discovery | [Property Tax-Exempt Parcels](https://datacatalog.cookcountyil.gov/d/vgzx-68gb) | `vgzx-68gb` | Provisional | Exemption includes private owners and is never proof of public ownership. |
| Zoning | [Zoning Districts (current)](https://data.cityofchicago.org/d/dj47-wfun) | `dj47-wfun` | Selected | Zoning is screening context, not development approval. |
| Transit | [CTA GTFS](https://www.transitchicago.com/developers/gtfs/) | GTFS ZIP | Selected | Scheduled service, governed by CTA's developer agreement. |
| Navigation | [Community Areas](https://data.cityofchicago.org/d/igwz-8jzy) | `igwz-8jzy` | Selected | Reporting geography only. |
| Active schools | [CPS School Locations SY2526](https://data.cityofchicago.org/d/pb6d-zzuh) | `pb6d-zzuh` | Selected | Points do not delineate entire school campuses. |
| Active parks | [Park Boundaries (current)](https://data.cityofchicago.org/d/ej32-qgdr) | `ej32-qgdr` | Provisional | Verify the stable source view and schema before ingestion. |
| Other civic uses | [Libraries](https://data.cityofchicago.org/d/x8fc-8rcq), [police](https://data.cityofchicago.org/d/z8bn-74gv), and [fire](https://data.cityofchicago.org/d/28km-gtjn) | Three Socrata datasets | Provisional | Facility points are warnings, not parcel ownership evidence. |
| Rights-of-way and utilities | No consolidated parcel-level publication found | — | Gap | Shape and tax class can prioritize review but cannot confirm operational use. |
| Basemap | [Protomaps basemap](https://docs.protomaps.com/basemaps/) | Hosted API or PMTiles | Basemap only | Do not derive analytical facts from the basemap. |

## Second-release source decisions

| Role | Source or method | ID/service | Decision | Key caution |
| --- | --- | --- | --- | --- |
| Frequent transit | Scheduled arrivals derived from [CTA GTFS](https://www.transitchicago.com/developers/gtfs/) | `derived:cta_gtfs:v1` | Selected | Measures schedules, not real-time reliability; the product still needs an adopted frequency threshold. |
| Buildings | [Building Footprints](https://data.cityofchicago.org/d/syp8-uezg) | `syp8-uezg` | Selected | Missing geometry does not prove vacancy; condition and vacancy fields may be incomplete. |
| Current use | Parcel-level evidence composite | `derived:current_use:v1` | Selected | Combine inventory status, assessor class, footprint coverage, and facility flags; never convert unknown to vacant. |
| Planning overlays | [Operational Chicago zoning service](https://gisapps.chicago.gov/arcgis/rest/services/ExternalApps/Zoning/MapServer) | Layers 2, 9, 13, 14 | Selected | Planned developments, special districts, and transit-served locations require policy interpretation. |
| ARO policy areas | [Affordable Requirements Ordinance](https://www.chicago.gov/city/en/sites/affordable-requirements-ordinance/home.html) | No polygon feed found | Gap | Do not digitize overview maps for parcel-level scoring. |
| Flood | [City FEMA Floodplain 2021](https://gisapps.chicago.gov/arcgis/rest/services/ExternalApps/Zoning/MapServer/11) | Layer 11 | Provisional | The snapshot may lag current FEMA determinations and must be cross-checked. |
| Wetlands | [National Wetlands Inventory](https://www.fws.gov/program/national-wetlands-inventory/web-mapping-services) | `Wetlands/MapServer/0` | Selected | Not a jurisdictional wetland determination; mapping vintage varies. |
| Brownfields | [Illinois EPA Brownfields](https://geoservices.epa.illinois.gov/arcgis/rest/services/Land/BrownfieldsService/MapServer/0) | Layer 0 | Selected | Program points are incomplete and do not show the full affected area. |
| Historic constraints | [Chicago Landmark Boundaries](https://gisapps.chicago.gov/arcgis/rest/services/ExternalApps/Zoning/MapServer/5) | Layer 5 | Selected | A hit triggers review rather than automatic exclusion. |
| Assessed value | [Cook County Assessed Values](https://datacatalog.cookcountyil.gov/d/uzyt-m557) | `uzyt-m557` | Provisional | Assessment is not market value or development cost; license is unspecified. |
| Sale history | [Cook County Parcel Sales](https://datacatalog.cookcountyil.gov/d/wvhk-k5uv) | `wvhk-k5uv` | Provisional | Filter nominal, multi-parcel, and non-arm's-length transfers; license is unspecified. |
| Utility capacity | No suitable public parcel-level source found | — | Gap | Nearby infrastructure does not prove capacity; retain `unknown`. |

### Derived transit frequency

The second release will calculate scheduled arrivals from `trips.txt`, `stop_times.txt`,
`calendar.txt`, and `calendar_dates.txt` for explicit reference dates and time windows. Store raw
scheduled-arrival counts by stop, route, service date, and window before applying any policy threshold.
This supports comparisons and future threshold changes without re-ingesting GTFS. Do not label a stop
"frequent" until the methodology records the threshold and coverage hours in a score-version change.

### Current use and buildings

There is no single authoritative current-land-use polygon source suitable for parcel scoring. The
registered `derived:current_use:v1` composite will combine City land status, Cook County assessor
class, building coverage, building status/vacancy evidence, and active-facility flags. Every component
retains its source date. Conflicts and sparse evidence produce `unknown` or a review flag—not a vacancy
classification.

### Environmental and historic screening

The City zoning service exposes polygon layers for its 2021 FEMA floodplain and landmark boundaries.
The flood layer is provisional because its date is explicit; before each release, compare it with the
current FEMA source and the independently dated flood field in the Cook County Parcel Universe.

National Wetlands Inventory polygons and Illinois EPA brownfield points provide additional warning
evidence. Neither supports an automatic hard exclusion: NWI is not a jurisdictional determination,
and a brownfield point neither defines contamination extent nor means remediation is impossible.
Likewise, landmark overlap indicates additional review rather than unbuildability.

### Policy context

Chicago's operational zoning service is preferred over static maps for planned developments, special
districts, and transit-served-location polygons. No authoritative machine-readable geometry was found
for all current Affordable Requirements Ordinance areas. Until the City publishes or supplies it,
overview maps must not be manually digitized for parcel-level scoring.

### Cost proxies

Assessed land value and parcel sales can provide limited context only. Display the assessment stage
and tax year, and never call assessed value an acquisition or development cost. Sales analysis must
retain deed type, multi-sale indicators, parcel count, and the Assessor's filter fields so nominal,
government, family, and multi-parcel transfers are not presented as ordinary comparables.

### Utility capacity

No authoritative publishable parcel-level water, sewer, electric, or gas capacity source was found in
the City catalog or agency materials reviewed. The tracker will store utility capacity as `unknown`.
It will not use proximity to a main, substation, or other mapped asset as a capacity proxy.

## Public-owner coverage

| Owner group | MVP coverage | Publication rule |
| --- | --- | --- |
| City of Chicago departments | Strongest current coverage through the City-Owned Land Inventory. | Publish records matched to an exact parcel PIN; retain the original managing organization and status. |
| CTA, CHA, CPS, Park District, Public Building Commission, and other local authorities | Partial. Some appear as managing organizations in the City inventory, but no complete consolidated ownership inventory was found. | A managing-organization value alone is not title evidence. Publish only exact-PIN records from an authoritative inventory or an independently verified agency record. |
| Cook County and its authorities/districts | Partial discovery through exempt-parcel owner names; no complete machine-readable owned-land inventory was found. | Require independent verification of the owner and exact PIN. Exempt status alone is insufficient. |
| State of Illinois and state agencies | Gap. No complete, current, parcel-level public inventory was found. Surplus-property pages cover selected offerings rather than all state land. | Require an agency record with an exact PIN. Keep unverified discoveries out of the published candidate layer. |
| Federal agencies | Deliberately excluded. | Run the explicit federal-owner classifier before candidate selection and retain the matching exclusion rule. Ambiguous names go to review rather than being guessed. |

This conservative policy makes early coverage uneven, but avoids presenting privately owned exempt
land or merely managed land as publicly owned. The unmatched and review queues will quantify the
gap rather than silently dropping it.

## Technical findings

### Parcel geometry and identifiers

Cook County GIS is the authoritative polygon source for the MVP. The current layer exposes polygon
geometry in Illinois State Plane East feet (EPSG:3435; the ArcGIS service reports WKID 102671),
`PIN14`, `Pin10`, `geom_year`, and edit dates. Responses are limited to 2,000 features, so the future
adapter must page using stable object IDs and filter to Chicago before publication.

The Assessor's current-year Parcel Universe provides 14- and 10-digit PINs, parcel centroids, class,
municipality, community area, tax districts, accessibility fields, and separately dated contextual
fields. It complements rather than replaces the polygon service.

The Cook County services do not state terms that clearly authorize redistribution. Development and
private testing can proceed against the service, but a public parcel-geometry download or bundled
derivative must wait for confirmation from `gis@cookcountyil.gov` and the Assessor regarding their
respective data.

### Ownership

The City inventory supplies a source record ID, PIN, managing organization, property status,
acquisition/disposition fields, listing state, area estimates, zoning, location, and last-update text.
Its own disclaimer makes clear that the data does not replace title, environmental, legal, or other
due diligence.

The Assessor's exempt-parcel dataset includes PIN, tax year, owner name, class, address, and a point.
Government land is only one category of exempt property, so this dataset creates research leads. A
record becomes a public-land candidate only after another authoritative source verifies its owner.

### Transit

CTA's GTFS feed contains stops, routes, trips, stop times, calendars, service exceptions, and route
shapes. CTA states that it generally updates the package every one or two weeks, sometimes more
often. The first ingestion should preserve each ZIP because CTA posts only one current/future package
at a time. Scheduled trip counts support the registered frequency metric described above.

### Active public use

The first release will use current school points, park polygons, and library/police/fire facility
points to identify likely active use. A spatial hit creates an `active_public_use` warning and review
record; it does not establish parcel ownership or automatically hard-exclude the parcel. Active use
must be confirmed against the ownership inventory and parcel context before applying the methodology's
20/100 score cap.

## Licensing and attribution policy

- Preserve the publisher, source page, dataset/service identifier, publisher update time, fetch time,
  checksum, row count, and pipeline version for every run.
- Display City of Chicago, Cook County, CTA, Chicago Park District, CPS, and OpenStreetMap/Protomaps
  attribution wherever their data appears.
- Do not copy raw source snapshots into Git.
- Do not expose raw Cook County parcel geometry as a download until redistribution terms are confirmed.
- CTA-derived transit features must comply with the
  [CTA Developer License Agreement](https://www.transitchicago.com/downloads/sch_data/developers_license_agreement.htm).
- OpenStreetMap-derived Protomaps tiles remain a visual basemap. Any future OSM analytical use needs a
  separate registry entry, reproducible extract date, and ODbL analysis.

## Open source questions

1. Obtain written Cook County guidance covering storage, transformation, display, and redistribution
   of the current parcel polygons and Assessor records.
2. Locate or request parcel-level inventories from CTA, CHA, CPS, Cook County, Illinois CMS, IDOT, and
   other relevant authorities. Record each response even if the agency has no machine-readable feed.
3. Confirm a stable source dataset and schema behind the Chicago Park District's current boundary map.
4. Decide whether public universities and independent districts are handled through agency-specific
   inventories or a verified exempt-parcel review workflow.
5. Request authoritative machine-readable ARO policy-area boundaries from the Department of Housing.
6. Re-check utilities-capacity availability before implementing infrastructure scoring; do not
   substitute asset proximity without evidence that it represents available capacity.
