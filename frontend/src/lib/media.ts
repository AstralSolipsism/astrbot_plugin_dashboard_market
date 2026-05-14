import type { MediaAsset } from '../types/market';

export type MediaMirrorLabel = 'mirrored' | 'mirrorFailed' | 'mirrorMissing' | 'source';

export function mediaAssetUrl(asset: MediaAsset | undefined, origin = browserOrigin()): string {
  return normalizeMarketMediaUrl(asset?.preferredUrl ?? asset?.url ?? '', origin);
}

export function mediaMirrorLabel(asset: MediaAsset | undefined): MediaMirrorLabel {
  if (!asset) {
    return 'source';
  }
  if (asset.mirrorStatus === 'mirrored') {
    return 'mirrored';
  }
  if (asset.mirrorStatus === 'failed') {
    return 'mirrorFailed';
  }
  if (asset.mirrorStatus === 'missing') {
    return 'mirrorMissing';
  }
  return 'source';
}

export function hasMediaMirrorFailure(assets: MediaAsset[]): boolean {
  return assets.some((asset) => asset.mirrorStatus === 'failed');
}

function normalizeMarketMediaUrl(url: string, origin: string | undefined): string {
  if (!url || !origin) {
    return url;
  }

  try {
    const parsed = new URL(url, origin);
    if ((parsed.protocol === 'http:' || parsed.protocol === 'https:') && parsed.pathname.startsWith('/media/')) {
      return `${origin.replace(/\/+$/, '')}${parsed.pathname}${parsed.search}${parsed.hash}`;
    }
  } catch {
    return url;
  }

  return url;
}

function browserOrigin(): string | undefined {
  return typeof window === 'undefined' ? undefined : window.location.origin;
}
