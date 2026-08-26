import { useEffect, useRef } from "react";
import {
  AttributionControl,
  Map,
  NavigationControl,
  addProtocol,
  removeProtocol,
} from "maplibre-gl";
import { Protocol } from "pmtiles";
import { createMapStyle } from "./mapStyle";

const CHICAGO_CENTER: [number, number] = [-87.6298, 41.8781];

export default function App() {
  const mapContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    const protocol = new Protocol();
    addProtocol("pmtiles", protocol.tile);

    const map = new Map({
      container: mapContainer.current,
      style: createMapStyle(import.meta.env.VITE_BASEMAP_URL),
      center: CHICAGO_CENTER,
      zoom: 10.2,
      attributionControl: false,
    });
    map.addControl(new NavigationControl(), "bottom-right");
    map.addControl(new AttributionControl({ compact: true }));

    return () => {
      map.remove();
      removeProtocol("pmtiles");
    };
  }, []);

  return (
    <main className="app-shell">
      <header className="masthead">
        <div>
          <p className="eyebrow">Chicago public land explorer</p>
          <h1>Land to Homes</h1>
        </div>
        <span className="release-badge">Foundation build</span>
      </header>

      <section className="workspace" aria-label="Land explorer">
        <aside className="intro-panel">
          <p className="eyebrow">Portfolio project · Methodology v1.0.0</p>
          <h2>Find public land with housing potential.</h2>
          <p>
            The data pipeline and parcel scoring are the next milestone. This scaffold establishes
            the API, PostGIS, MapLibre, and Protomaps foundation.
          </p>
          <dl>
            <div>
              <dt>Geography</dt>
              <dd>City of Chicago</dd>
            </div>
            <div>
              <dt>Views</dt>
              <dd>Parcels + assembled sites</dd>
            </div>
            <div>
              <dt>Refresh target</dt>
              <dd>Daily</dd>
            </div>
          </dl>
          {!import.meta.env.VITE_BASEMAP_URL && (
            <p className="setup-note" role="status">
              Add <code>VITE_BASEMAP_URL</code> to display a PMTiles basemap.
            </p>
          )}
        </aside>

        <div ref={mapContainer} className="map" aria-label="Map of Chicago" />
      </section>
    </main>
  );
}
