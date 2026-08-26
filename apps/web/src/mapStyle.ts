import type { StyleSpecification } from "maplibre-gl";
import layers from "protomaps-themes-base";

export type BasemapMode = "api" | "pmtiles" | "empty";

export interface BasemapStyle {
  mode: BasemapMode;
  style: StyleSpecification | string;
}

interface BasemapOptions {
  apiKey: string | undefined;
  basemapUrl: string | undefined;
}

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

export function createMapStyle({ apiKey, basemapUrl }: BasemapOptions): BasemapStyle {
  if (apiKey) {
    return {
      mode: "api",
      style: `https://api.protomaps.com/styles/v5/light/en.json?key=${encodeURIComponent(apiKey)}`,
    };
  }

  if (!basemapUrl) return { mode: "empty", style: emptyStyle };

  return {
    mode: "pmtiles",
    style: {
      version: 8,
      glyphs: "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf",
      sprite: "https://protomaps.github.io/basemaps-assets/sprites/v4/light",
      sources: {
        protomaps: {
          type: "vector",
          url: `pmtiles://${basemapUrl}`,
          attribution:
            '<a href="https://protomaps.com">Protomaps</a> © <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>',
        },
      },
      layers: layers("protomaps", "light", "en") as StyleSpecification["layers"],
    },
  };
}
