export interface AstrBotPluginPageContext {
  pluginName?: string;
  displayName?: string;
  pageName?: string;
  pageTitle?: string;
  locale?: string;
  i18n?: Record<string, unknown>;
}

export interface AstrBotPluginPageBridge {
  ready(): Promise<AstrBotPluginPageContext>;
  getContext?(): AstrBotPluginPageContext | null;
  getLocale?(): string;
  getI18n?(): Record<string, unknown>;
  t?(key: string, fallback?: string): string;
  onContext?(handler: (context: AstrBotPluginPageContext | null) => void): () => void;
  openExternal?(url: string): void | Promise<void>;
  openUrl?(url: string): void | Promise<void>;
  openURL?(url: string): void | Promise<void>;
  apiGet<T = unknown>(endpoint: string, params?: Record<string, unknown>): Promise<T>;
  apiPost<T = unknown>(endpoint: string, body?: unknown): Promise<T>;
}

export function getPluginBridge(): AstrBotPluginPageBridge {
  const bridge = window.AstrBotPluginPage;
  if (!bridge) {
    throw new Error('AstrBotPluginPage bridge is unavailable.');
  }
  return bridge;
}
