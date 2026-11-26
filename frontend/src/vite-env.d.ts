/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Only if the Flask API is on a different domain than the site (not needed on Vercel) */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
