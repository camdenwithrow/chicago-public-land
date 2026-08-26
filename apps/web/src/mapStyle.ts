import type { StyleSpecification } from "maplibre-gl";
import layers from "protomaps-themes-base";

const emptyStyle: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#e8e6df" },
    },
  ],
};

export function createMapStyle(basemapUrl: string | undefined): StyleSpecification {
  if (!basemapUrl) return emptyStyle;

  return {
    version: 8,
    glyphs: "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf",
    sources: {
      protomaps: {
        type: "vector",
        url: `pmtiles://${basemapUrl}`,
        attribution:
          '<a href="https://openstreetmap.org/copyright">© OpenStreetMap contributors</a>',
      },
    },
    layers: layers("protomaps", "light", "en") as StyleSpecification["layers"],
  };
}
