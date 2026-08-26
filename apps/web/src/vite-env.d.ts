/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_PROTOMAPS_API_KEY?: string;
  readonly VITE_BASEMAP_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
