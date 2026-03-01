// frontend/types/gtag.d.ts

interface Window {
  gtag?: (...args: unknown[]) => void;
  dataLayer?: object[];
}
