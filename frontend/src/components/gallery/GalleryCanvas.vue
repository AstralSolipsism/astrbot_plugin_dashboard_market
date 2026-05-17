<script setup lang="ts">
import { computed, useTemplateRef } from 'vue';
import type { DashboardInstallDisplayState, DashboardRegistryVersion, MediaAsset } from '../../types/market';
import { useI18n } from '../../composables/useI18n';
import { useInfiniteCanvas } from '../../composables/useInfiniteCanvas';
import { useResponsiveGalleryLayout } from '../../composables/useResponsiveGalleryLayout';
import type { GalleryItem } from '../../types/gallery';
import GalaxyBackdrop from './GalaxyBackdrop.vue';
import GalleryCard from './GalleryCard.vue';
import GalleryHero from './GalleryHero.vue';
import { hasMediaMirrorFailure, mediaAssetUrl } from '../../lib/media';

interface GalleryStats {
  total: number;
  passed: number;
  contracts: number;
}

interface PlaceholderSeed {
  key: string;
  status: string;
}

interface GridSlot {
  col: number;
  row: number;
}

const props = defineProps<{
  dashboards: DashboardRegistryVersion[];
  error: string;
  installStates: Record<string, DashboardInstallDisplayState>;
  loading: boolean;
  stats: GalleryStats;
}>();

const emit = defineEmits<{
  browse: [];
  retry: [];
  select: [item: GalleryItem];
  submit: [];
}>();

const marketRepoUrl = 'https://github.com/AstralSolipsism/astrbot_dashboard_market';
const gridSlots = createGridSlots();

const placeholderSeeds: PlaceholderSeed[] = [
  {
    key: 'contractAtlas',
    status: 'concept'
  },
  {
    key: 'pluginConsole',
    status: 'concept'
  },
  {
    key: 'providerStudio',
    status: 'concept'
  },
  {
    key: 'chatSurface',
    status: 'concept'
  },
  {
    key: 'platformSwitchboard',
    status: 'concept'
  },
  {
    key: 'settingsLedger',
    status: 'concept'
  },
  {
    key: 'mobilePreview',
    status: 'concept'
  },
  {
    key: 'releaseWall',
    status: 'concept'
  },
  {
    key: 'validationRoom',
    status: 'concept'
  },
  {
    key: 'dashboardMarket',
    status: 'concept'
  },
  {
    key: 'bridgeLab',
    status: 'concept'
  },
  {
    key: 'runtimeMonitor',
    status: 'concept'
  },
  {
    key: 'authThreshold',
    status: 'concept'
  },
  {
    key: 'modelBench',
    status: 'concept'
  },
  {
    key: 'toolLibrary',
    status: 'concept'
  },
  {
    key: 'memoryDeck',
    status: 'concept'
  },
  {
    key: 'webhookConsole',
    status: 'concept'
  },
  {
    key: 'personaShelf',
    status: 'concept'
  },
  {
    key: 'logCorridor',
    status: 'concept'
  },
  {
    key: 'artifactTable',
    status: 'concept'
  },
  {
    key: 'capabilityMap',
    status: 'concept'
  },
  {
    key: 'previewBoard',
    status: 'concept'
  },
  {
    key: 'pluginBridge',
    status: 'concept'
  },
  {
    key: 'routeIndex',
    status: 'concept'
  }
];

const fallbackPlaceholder: PlaceholderSeed = {
  key: 'dashboardTile',
  status: 'concept'
};

const { t } = useI18n();
const canvasRef = useTemplateRef<HTMLElement>('canvas');
const { layout, layoutStyle } = useResponsiveGalleryLayout(canvasRef);
const { isDragging, onPointerDown, onPointerMove, onPointerUp, onWheel, planeStyle, shouldSuppressClick } =
  useInfiniteCanvas();

const galleryItems = computed<GalleryItem[]>(() => {
  const dashboards = props.dashboards.map((dashboard, index) => {
    const position = positionFor(index);
    return {
      id: `${dashboard.id}@${dashboard.version}`,
      title: dashboard.project.name,
      description: dashboard.project.description,
      imageUrl: resolveImage(dashboard),
      authorId: resolveAuthorId(dashboard),
      repositoryUrl: resolveRepositoryUrl(dashboard),
      visualSeed: stableVisualSeed(`${dashboard.id}@${dashboard.version}`, index),
      x: position.x,
      y: position.y,
      status: dashboard.verification.status,
      previewFailed: hasMediaMirrorFailure(
        [dashboard.media.effectiveCover, ...dashboard.media.effectiveScreenshots].filter(
          (asset): asset is MediaAsset => Boolean(asset)
        )
      ),
      installState: props.installStates[`${dashboard.id}@${dashboard.version}`] ?? 'none',
      dashboard
    };
  });

  const targetCount = Math.max(132, dashboards.length);
  const placeholders = Array.from({ length: Math.max(0, targetCount - dashboards.length) }, (_, index) => {
    const seed = placeholderFor(index);
    const itemIndex = dashboards.length + index;
    const position = positionFor(itemIndex);
    const title = placeholderTitle(seed, index);
    return {
      id: `placeholder-${index}`,
      title,
      description: placeholderDescription(seed),
      authorId: '@market',
      repositoryUrl: marketRepoUrl,
      visualSeed: stableVisualSeed(seed.key, itemIndex),
      x: position.x,
      y: position.y,
      status: seed.status
    };
  });

  return [...dashboards, ...placeholders];
});

function createGridSlots(): GridSlot[] {
  const slots: GridSlot[] = [];
  for (let row = -6; row <= 6; row += 1) {
    for (let col = -8; col <= 8; col += 1) {
      if (isHeroReservedSlot(col, row)) {
        continue;
      }
      slots.push({ col, row });
    }
  }

  return slots.sort(compareGallerySlots);
}

function compareGallerySlots(a: GridSlot, b: GridSlot): number {
  const centerRowPriority = Number(a.row !== 0) - Number(b.row !== 0);
  if (centerRowPriority !== 0) {
    return centerRowPriority;
  }

  const colDistance = Math.abs(a.col) - Math.abs(b.col);
  if (colDistance !== 0) {
    return colDistance;
  }

  if (a.row === 0 && b.row === 0) {
    return a.col - b.col;
  }

  const rowDistance = Math.abs(a.row) - Math.abs(b.row);
  if (rowDistance !== 0) {
    return rowDistance;
  }

  if (a.row !== b.row) {
    return a.row - b.row;
  }

  return a.col - b.col;
}

function isHeroReservedSlot(col: number, row: number): boolean {
  return col === 0 && row === 0;
}

function positionFor(index: number): { x: number; y: number } {
  const slot = gridSlots[index % gridSlots.length] ?? { col: 0, row: 0 };
  const ring = Math.floor(index / gridSlots.length);
  const ringDirection = index % 2 === 0 ? 1 : -1;
  const { gridX, gridY } = layout.value;

  return {
    x: (slot.col + ring * 17 * ringDirection) * gridX,
    y: slot.row * gridY
  };
}

function placeholderFor(index: number): PlaceholderSeed {
  return placeholderSeeds[index % placeholderSeeds.length] ?? fallbackPlaceholder;
}

function placeholderTitle(seed: PlaceholderSeed, index: number): string {
  const repeat = Math.floor(index / placeholderSeeds.length);
  const title = t(`placeholder.${seed.key}.title`);
  if (repeat === 0) {
    return title;
  }

  return `${title} ${String(repeat + 1).padStart(2, '0')}`;
}

function placeholderDescription(seed: PlaceholderSeed): string {
  return t(`placeholder.${seed.key}.description`);
}

function resolveImage(dashboard: DashboardRegistryVersion): string | undefined {
  return mediaAssetUrl(dashboard.media.effectiveCover ?? dashboard.media.effectiveScreenshots[0]) || undefined;
}

function resolveAuthorId(dashboard: DashboardRegistryVersion): string {
  const authorName = dashboard.project.authors[0]?.name.trim() || dashboard.id;
  return authorName.startsWith('@') ? authorName : `@${authorName}`;
}

function resolveRepositoryUrl(dashboard: DashboardRegistryVersion): string {
  return dashboard.source.repo;
}

function stableVisualSeed(value: string, index: number): number {
  let seed = index + 1;
  for (let i = 0; i < value.length; i += 1) {
    seed = (seed * 31 + value.charCodeAt(i)) >>> 0;
  }
  return seed;
}

function selectItem(item: GalleryItem): void {
  if (shouldSuppressClick()) {
    return;
  }

  emit('select', item);
}
</script>

<template>
  <section
    ref="canvas"
    class="gallery-canvas"
    :class="{ 'is-dragging': isDragging }"
    :data-compact="layout.navCompact"
    :style="layoutStyle"
    :aria-label="t('gallery.label')"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @wheel="onWheel"
  >
    <GalaxyBackdrop
      class="gallery-canvas__galaxy"
      :auto-center-repulsion="1"
      :density="1.2"
      :glow-intensity="0.6"
      :hue-shift="120"
      :mouse-interaction="true"
      :mouse-repulsion="false"
      :repulsion-strength="2"
      :rotation-speed="0.1"
      :saturation="0.6"
      :speed="1"
      :star-speed="0.5"
      :twinkle-intensity="0.6"
    />
    <div class="gallery-canvas__grid" aria-hidden="true"></div>
    <div class="gallery-canvas__plane" :style="planeStyle">
      <GalleryHero
        @browse="emit('browse')"
        @submit="emit('submit')"
      />
      <div
        v-for="item in galleryItems"
        :key="item.id"
        class="gallery-canvas__node"
        :style="{ left: `${item.x}px`, top: `${item.y}px` }"
      >
        <GalleryCard :item="item" @select="selectItem" />
      </div>
    </div>

    <section v-if="error" class="gallery-canvas__notice" role="status" data-no-pan="true">
      <span>{{ t('gallery.registryUnavailable') }}</span>
      <button type="button" @click="emit('retry')">{{ t('gallery.retry') }}</button>
    </section>
  </section>
</template>

<style scoped>
.gallery-canvas {
  --gallery-scale: 1;
  --gallery-card-width: 416px;
  --gallery-card-height: 260px;
  --gallery-card-hover-scale: 1.1;
  --gallery-grid-x: 480px;
  --gallery-grid-y: 324px;
  position: fixed;
  inset: 0;
  overflow: hidden;
  background: oklch(0.08 0.018 245);
  cursor: grab;
  touch-action: none;
}

.gallery-canvas.is-dragging {
  cursor: grabbing;
}

.gallery-canvas__grid {
  position: absolute;
  z-index: 1;
  inset: -200%;
  background-image:
    linear-gradient(oklch(0.88 0.018 210 / 8%) 1px, transparent 1px),
    linear-gradient(90deg, oklch(0.88 0.018 210 / 8%) 1px, transparent 1px);
  background-size: var(--gallery-grid-x) var(--gallery-grid-y);
  opacity: 0.34;
  pointer-events: none;
}

.gallery-canvas__plane {
  position: absolute;
  z-index: 2;
  inset-block-start: 50%;
  inset-inline-start: 50%;
  inline-size: 0;
  block-size: 0;
  transform: translate3d(var(--pan-x), var(--pan-y), 0);
  transform-origin: center;
  will-change: transform;
}

.gallery-canvas__galaxy {
  z-index: 0;
}

.gallery-canvas__node {
  position: absolute;
  z-index: 1;
  inline-size: var(--gallery-card-width);
  block-size: var(--gallery-card-height);
  transform: translate(-50%, -50%);
}

.gallery-canvas__node:hover,
.gallery-canvas__node:focus-within {
  z-index: 10;
}

.gallery-canvas__notice {
  position: fixed;
  z-index: 45;
  inset-inline-start: 24px;
  inset-block-end: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid oklch(0.78 0.045 80 / 80%);
  border-radius: 999px;
  background: oklch(0.96 0.035 88 / 88%);
  box-shadow: 0 18px 46px oklch(0.18 0.006 110 / 12%);
  color: oklch(0.25 0.035 80);
  padding: 6px 6px 6px 16px;
  backdrop-filter: blur(14px);
}

.gallery-canvas__notice span,
.gallery-canvas__notice button {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
}

.gallery-canvas__notice button {
  min-block-size: 34px;
  border: 0;
  border-radius: 999px;
  background: oklch(0.18 0.004 110);
  color: oklch(0.97 0.006 110);
  cursor: pointer;
  padding-inline: 14px;
}

@media (max-width: 720px) {
  .gallery-canvas__grid {
    opacity: 0.22;
  }

  .gallery-canvas__node {
    inline-size: var(--gallery-card-width);
    block-size: var(--gallery-card-height);
  }

  .gallery-canvas__notice {
    inset-inline: 12px;
    inset-block-end: 12px;
    justify-content: space-between;
  }
}
</style>
