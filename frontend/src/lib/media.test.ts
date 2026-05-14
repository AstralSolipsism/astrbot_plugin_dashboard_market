import { describe, expect, it } from 'vitest';
import { mediaAssetUrl, mediaMirrorLabel } from './media';

describe('site media helpers', () => {
  it('prefers market media mirror urls when available', () => {
    expect(
      mediaAssetUrl({
        url: 'https://example.com/source.png',
        preferredUrl: './media/demo/1.0.0/cover.png',
        alt: 'Cover',
        source: 'author',
        sha256: 'a'.repeat(64)
      })
    ).toBe('./media/demo/1.0.0/cover.png');
  });

  it('uses the current origin for market-hosted media mirrors', () => {
    expect(
      mediaAssetUrl(
        {
          url: 'registry/media/demo/1.0.0/cover.png',
          preferredUrl: 'https://dashboard-market.example.com/media/demo/1.0.0/cover.png',
          alt: 'Cover',
          source: 'author',
          sha256: 'a'.repeat(64)
        },
        'http://192.168.50.149:40009'
      )
    ).toBe('http://192.168.50.149:40009/media/demo/1.0.0/cover.png');
  });

  it('falls back to the source url and labels failed mirrors clearly', () => {
    const asset = {
      url: 'https://example.com/source.png',
      alt: 'Cover',
      source: 'author' as const,
      sha256: 'a'.repeat(64),
      mirrorStatus: 'failed' as const
    };

    expect(mediaAssetUrl(asset)).toBe('https://example.com/source.png');
    expect(mediaMirrorLabel(asset)).toBe('mirrorFailed');
  });
});
