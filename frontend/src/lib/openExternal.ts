type ExternalOpener = (url: string) => void | Promise<void>;

type ExternalBridge = {
  openExternal?: ExternalOpener;
  openUrl?: ExternalOpener;
  openURL?: ExternalOpener;
};

function normalizeExternalUrl(value?: string | null): string | undefined {
  if (!value) {
    return undefined;
  }

  try {
    const url = new URL(value);
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      return undefined;
    }

    return url.href;
  } catch {
    return undefined;
  }
}

function openWithWindow(url: string): void {
  window.open(url, '_blank', 'noopener,noreferrer');
}

export function openExternalUrl(value?: string | null): void {
  const url = normalizeExternalUrl(value);
  if (!url) {
    return;
  }

  const bridge = (window as Window & { AstrBotPluginPage?: ExternalBridge }).AstrBotPluginPage;
  const opener = bridge?.openExternal ?? bridge?.openUrl ?? bridge?.openURL;

  if (opener) {
    try {
      const result = opener(url);
      if (result && typeof result.catch === 'function') {
        void result.catch(() => openWithWindow(url));
      }
      return;
    } catch {
      openWithWindow(url);
      return;
    }
  }

  openWithWindow(url);
}
