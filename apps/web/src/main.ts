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

window.addEventListener(
  "beforeunload",
  () => {
    map.remove();
    if (protocol) removeProtocol("pmtiles");
  },
  { once: true },
);
