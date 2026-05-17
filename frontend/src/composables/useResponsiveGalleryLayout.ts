import { computed, onBeforeUnmount, onMounted, shallowRef, type ShallowRef } from 'vue';

interface GalleryViewport {
  height: number;
  width: number;
}

export interface ResponsiveGalleryLayout {
  cardHeight: number;
  cardWidth: number;
  compact: boolean;
  gridX: number;
  gridY: number;
  hoverScale: number;
  navCompact: boolean;
  scale: number;
  tight: boolean;
}

const baseViewport = {
  height: 720,
  width: 1180
};

const baseCard = {
  height: 260,
  width: 416
};

const baseGrid = {
  x: 480,
  y: 324
};

export function useResponsiveGalleryLayout(target: Readonly<ShallowRef<HTMLElement | null>>) {
  const viewport = shallowRef<GalleryViewport>(baseViewport);
  let observer: ResizeObserver | undefined;

  const layout = computed<ResponsiveGalleryLayout>(() => {
    const width = Math.max(1, viewport.value.width);
    const height = Math.max(1, viewport.value.height);
    const tight = width < 1040 || height < 580;
    const compact = width < 1320 || height < 700;
    const minScale = width < 520 ? 0.62 : compact ? 0.72 : 0.78;
    const scale = round(clamp(Math.min(width / baseViewport.width, height / baseViewport.height), minScale, 1), 3);
    const gridCompression = tight ? 0.84 : compact ? 0.86 : 1;
    const verticalCompression = height < 620 ? 0.9 : height < 700 ? 0.96 : 1;

    return {
      cardHeight: Math.round(baseCard.height * scale),
      cardWidth: Math.round(baseCard.width * scale),
      compact,
      gridX: Math.round(baseGrid.x * scale * gridCompression),
      gridY: Math.round(baseGrid.y * scale * verticalCompression),
      hoverScale: tight ? 1.045 : compact ? 1.07 : 1.1,
      navCompact: width < 980 || height < 660,
      scale,
      tight
    };
  });

  const layoutStyle = computed<Record<string, string>>(() => {
    const current = layout.value;
    const cardInset = clamp(Math.round(14 * current.scale), 9, 14);
    const controlHeight = clamp(Math.round(34 * current.scale), 28, 34);
    const badgeHeight = clamp(Math.round(30 * current.scale), 24, 30);

    return {
      '--gallery-card-badge-height': `${badgeHeight}px`,
      '--gallery-card-badge-max-width': `${clamp(Math.round(178 * current.scale), 116, 178)}px`,
      '--gallery-card-control-height': `${controlHeight}px`,
      '--gallery-card-font-size': `${clamp(Math.round(12 * current.scale), 11, 12)}px`,
      '--gallery-card-height': `${current.cardHeight}px`,
      '--gallery-card-hover-scale': current.hoverScale.toFixed(3),
      '--gallery-card-inset': `${cardInset}px`,
      '--gallery-card-meta-gap': `${clamp(Math.round(10 * current.scale), 6, 10)}px`,
      '--gallery-card-radius': `${clamp(Math.round(8 * current.scale), 6, 8)}px`,
      '--gallery-card-width': `${current.cardWidth}px`,
      '--gallery-grid-x': `${current.gridX}px`,
      '--gallery-grid-y': `${current.gridY}px`,
      '--gallery-hero-action-gap': `${clamp(Math.round(14 * current.scale), 8, 14)}px`,
      '--gallery-hero-action-height': `${clamp(Math.round(28 * current.scale), 24, 28)}px`,
      '--gallery-hero-action-size': `${clamp(Math.round(12 * current.scale), 10, 12)}px`,
      '--gallery-hero-gap': `${clamp(Math.round(12 * current.scale), 7, 12)}px`,
      '--gallery-hero-lead-size': `${clamp(Math.round(13 * current.scale), 11, 13)}px`,
      '--gallery-hero-pad': `${clamp(Math.round(28 * current.scale), 12, 28)}px`,
      '--gallery-hero-title-size': `${clamp(Math.round(50 * current.scale), 28, 50)}px`,
      '--gallery-scale': current.scale.toString()
    };
  });

  function updateViewport(): void {
    const element = target.value;
    viewport.value = {
      height: Math.round(element?.clientHeight || getWindowSize().height || baseViewport.height),
      width: Math.round(element?.clientWidth || getWindowSize().width || baseViewport.width)
    };
  }

  onMounted(() => {
    updateViewport();
    const element = target.value;
    if (element && typeof ResizeObserver !== 'undefined') {
      observer = new ResizeObserver(updateViewport);
      observer.observe(element);
    }
    window.addEventListener('resize', updateViewport, { passive: true });
  });

  onBeforeUnmount(() => {
    observer?.disconnect();
    window.removeEventListener('resize', updateViewport);
  });

  return {
    layout,
    layoutStyle
  };
}

function getWindowSize(): GalleryViewport {
  if (typeof window === 'undefined') {
    return baseViewport;
  }
  return {
    height: window.innerHeight,
    width: window.innerWidth
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function round(value: number, precision: number): number {
  const factor = 10 ** precision;
  return Math.round(value * factor) / factor;
}
