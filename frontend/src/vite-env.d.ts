/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the Flask API in production, e.g. https://waikiki-api.onrender.com */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
