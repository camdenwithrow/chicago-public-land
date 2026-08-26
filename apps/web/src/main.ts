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

const basemapUrl = import.meta.env.VITE_BASEMAP_URL?.trim() || undefined;
if (basemapUrl) {
  document.querySelector("#basemap-note")?.remove();
}

const protocol = new Protocol();
addProtocol("pmtiles", protocol.tile);

const map = new Map({
  container: mapContainer,
  style: createMapStyle(basemapUrl),
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
    removeProtocol("pmtiles");
  },
  { once: true },
);
