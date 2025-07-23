/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  // додайте тут інші змінні середовища, якщо потрібно
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}