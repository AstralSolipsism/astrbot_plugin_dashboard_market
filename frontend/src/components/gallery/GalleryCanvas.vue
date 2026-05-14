<script setup lang="ts">
import { computed } from 'vue';
import type { DashboardInstallDisplayState, DashboardRegistryVersion, MediaAsset } from '../../types/market';
import { useI18n } from '../../composables/useI18n';
import { useInfiniteCanvas } from '../../composables/useInfiniteCanvas';
import type { GalleryItem } from '../../types/gallery';
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

const gridStep = {
  x: 480,
  y: 324
};

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
const { isDragging, onPointerDown, onPointerMove, onPointerUp, onWheel, planeStyle, shouldSuppressClick } =
  useInfiniteCanvas();

const galleryItems = computed<GalleryItem[]>(() => {
  const dashboards = props.dashboards.map((dashboard, index) => {
    const position = positionFor(index);
    return {
      id: `${dashboard.id}@${dashboard.version}`,
      title: dashboard.project.name,
      description: dashboard.project.description,
      imageUrl: resolveImage(dashboard, index),
      authorId: resolveAuthorId(dashboard),
      repositoryUrl: resolveRepositoryUrl(dashboard),
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
      imageUrl: createPlaceholderImage(title, itemIndex),
      authorId: '@market',
      repositoryUrl: marketRepoUrl,
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

  return {
    x: (slot.col + ring * 17 * ringDirection) * gridStep.x,
    y: slot.row * gridStep.y
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

function resolveImage(dashboard: DashboardRegistryVersion, index: number): string {
  return (
    mediaAssetUrl(dashboard.media.effectiveCover ?? dashboard.media.effectiveScreenshots[0]) ||
    createPlaceholderImage(dashboard.project.name, index)
  );
}

function resolveAuthorId(dashboard: DashboardRegistryVersion): string {
  const authorName = dashboard.project.authors[0]?.name.trim() || dashboard.id;
  return authorName.startsWith('@') ? authorName : `@${authorName}`;
}

function resolveRepositoryUrl(dashboard: DashboardRegistryVersion): string {
  return dashboard.source.repo;
}

function createPlaceholderImage(title: string, index: number): string {
  const palette = [
    ['#f4f3ee', '#d8d6ce', '#191918', '#ede9de'],
    ['#efefec', '#c9cbc4', '#20211f', '#e5e8e1'],
    ['#f5f1ea', '#d1c8ba', '#181713', '#eee3d4'],
    ['#f2f4f1', '#c5d0c8', '#171c18', '#e1e9e4']
  ] as const;
  const [background, line, ink, panel] = palette[index % palette.length] ?? palette[0];
  const variant = index % 6;
  const escapedTitle = escapeSvg(truncateSvgLabel(title));
  const escapedCode = escapeSvg(`DM-${String(index + 1).padStart(3, '0')}`);
  const featureBlocks = [
    '<path d="M92 122h218v150H92zM342 122h286v72H342zM342 224h118v48H342zM488 224h140v48H488z" fill="none"/>',
    '<path d="M96 112h148v188H96zM278 112h148v188H278zM460 112h164v188H460z" fill="none"/>',
    '<path d="M92 128h536v56H92zM92 218h178v76H92zM308 218h320v76H308z" fill="none"/>',
    '<path d="M110 116h500v170H110zM142 148h118v106H142zM290 148h288v24H290zM290 206h228v24H290z" fill="none"/>',
    '<path d="M92 126h200v48H92zM92 206h200v48H92zM330 126h298v128H330z" fill="none"/>',
    '<path d="M126 112h468v42H126zM126 190h118v92H126zM286 190h118v92H286zM446 190h148v92H446z" fill="none"/>'
  ];
  const featuredBlock = featureBlocks[variant] ?? featureBlocks[0];
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="720" height="450" viewBox="0 0 720 450">
      <rect width="720" height="450" fill="${background}"/>
      <path d="M70 76H650M70 148H650M70 220H650M70 292H650M70 364H650" stroke="${line}" stroke-width="1"/>
      <path d="M104 76h512" stroke="${ink}" stroke-width="2" stroke-linecap="round"/>
      <rect x="84" y="96" width="552" height="224" rx="18" fill="${panel}" stroke="${ink}" stroke-width="2"/>
      <g stroke="${ink}" stroke-width="2" stroke-linejoin="round">${featuredBlock}</g>
      <circle cx="584" cy="284" r="14" fill="${ink}"/>
      <path d="M112 320h116M112 344h248" stroke="${line}" stroke-width="8" stroke-linecap="round"/>
      <text x="108" y="62" fill="${ink}" font-family="Inter, Arial, sans-serif" font-size="28" font-weight="760">${escapedTitle}</text>
      <text x="536" y="62" fill="${ink}" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700">${escapedCode}</text>
    </svg>
  `;

  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function truncateSvgLabel(value: string): string {
  const maxLength = 24;
  return value.length > maxLength ? `${value.slice(0, maxLength - 1)}...` : value;
}

function escapeSvg(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
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
    class="gallery-canvas"
    :class="{ 'is-dragging': isDragging }"
    :aria-label="t('gallery.label')"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @wheel="onWheel"
  >
    <div class="gallery-canvas__grid" aria-hidden="true"></div>
    <div class="gallery-canvas__plane" :style="planeStyle">
      <GalleryHero
        :loading="loading"
        :passed="stats.passed"
        :total="stats.total"
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
  --gallery-card-width: 416px;
  --gallery-card-height: 260px;
  --gallery-grid-x: 480px;
  --gallery-grid-y: 324px;
  position: fixed;
  inset: 0;
  overflow: hidden;
  background: oklch(0.97 0.006 110);
  cursor: grab;
  touch-action: none;
}

.gallery-canvas.is-dragging {
  cursor: grabbing;
}

.gallery-canvas__grid {
  position: absolute;
  inset: -200%;
  background-image:
    linear-gradient(oklch(0.56 0.006 110 / 6%) 1px, transparent 1px),
    linear-gradient(90deg, oklch(0.56 0.006 110 / 6%) 1px, transparent 1px);
  background-size: var(--gallery-grid-x) var(--gallery-grid-y);
  opacity: 0.18;
  pointer-events: none;
}

.gallery-canvas__plane {
  position: absolute;
  inset-block-start: 50%;
  inset-inline-start: 50%;
  inline-size: 0;
  block-size: 0;
  transform: translate3d(var(--pan-x), var(--pan-y), 0);
  transform-origin: center;
  will-change: transform;
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
