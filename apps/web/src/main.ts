import {
  AttributionControl,
  Map,
  NavigationControl,
  addProtocol,
  removeProtocol,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";
import "./styles.css";
import { createMapStyle } from "./mapStyle";

const CHICAGO_CENTER: [number, number] = [-87.6298, 41.8781];
const mapContainer = document.querySelector<HTMLElement>("#map");

interface SourceMetadata {
  key: string;
  name: string;
  publisher: string;
  source_url: string;
  source_updated_at: string | null;
  fetched_at: string | null;
}

interface TrackerMetadata {
  methodology_version: string;
  registry_version: string;
  tracker_processed_at: string | null;
  sources: SourceMetadata[];
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

async function loadMetadata(): Promise<void> {
  const metadataState = document.querySelector<HTMLElement>("#metadata-state");
  const sourceDates = document.querySelector<HTMLUListElement>("#source-dates");
  const processedAt = document.querySelector<HTMLElement>("#tracker-processed-at");
  const methodologyVersion = document.querySelector<HTMLElement>("#methodology-version");
  const registryVersion = document.querySelector<HTMLElement>("#registry-version");
  if (!metadataState || !sourceDates || !processedAt || !methodologyVersion || !registryVersion) {
    return;
  }

  const apiUrl = (import.meta.env.VITE_API_URL?.trim() || "http://localhost:8000").replace(/\/$/, "");
  try {
    const response = await fetch(`${apiUrl}/meta`);
    if (!response.ok) throw new Error(`metadata request returned ${response.status}`);
    const metadata = (await response.json()) as TrackerMetadata;
    methodologyVersion.textContent = metadata.methodology_version;
    registryVersion.textContent = metadata.registry_version;
    processedAt.textContent = metadata.tracker_processed_at
      ? formatDate(metadata.tracker_processed_at)
      : "Awaiting first ingestion";

    const currentSources = metadata.sources.filter(
      (source): source is SourceMetadata & { fetched_at: string } => source.fetched_at !== null,
    );
    if (currentSources.length === 0) {
      metadataState.textContent =
        "No source has been ingested yet. Publisher dates will appear separately from tracker processing dates.";
      return;
    }

    metadataState.textContent = `${currentSources.length} source ${currentSources.length === 1 ? "snapshot" : "snapshots"} available.`;
    for (const source of currentSources) {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = source.source_url;
      link.textContent = source.name;
      link.className = "font-medium underline decoration-emerald-800/30 underline-offset-2";
      const date = document.createElement("span");
      date.className = "mt-0.5 block text-emerald-950/55";
      date.textContent = source.source_updated_at
        ? `Publisher updated ${formatDate(source.source_updated_at)} · fetched ${formatDate(source.fetched_at)}`
        : `Publisher date unavailable · fetched ${formatDate(source.fetched_at)}`;
      item.append(link, date);
      sourceDates.append(item);
    }
  } catch {
    registryVersion.textContent = "Unavailable";
    metadataState.textContent =
      "Freshness metadata is unavailable. Start the API to load independently tracked source dates.";
  }
}

if (!mapContainer) {
  throw new Error("The map container is missing from the document.");
}

const basemap = createMapStyle({
  apiKey: import.meta.env.VITE_PROTOMAPS_API_KEY?.trim() || undefined,
  basemapUrl: import.meta.env.VITE_BASEMAP_URL?.trim() || undefined,
});

if (basemap.mode !== "empty") {
  document.querySelector("#basemap-note")?.remove();
}

let protocol: Protocol | undefined;
if (basemap.mode === "pmtiles") {
  protocol = new Protocol();
  addProtocol("pmtiles", protocol.tile);
}

const map = new Map({
  container: mapContainer,
  style: basemap.style,
  center: CHICAGO_CENTER,
  zoom: 10.2,
  attributionControl: false,
});

map.addControl(new NavigationControl(), "bottom-right");
map.addControl(new AttributionControl({ compact: true }));
void loadMetadata();

window.addEventListener(
  "beforeunload",
  () => {
    map.remove();
    if (protocol) removeProtocol("pmtiles");
  },
  { once: true },
);
