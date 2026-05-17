<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue';
import { useI18n } from '../../composables/useI18n';
import { mediaAssetUrl } from '../../lib/media';
import type { MediaAsset } from '../../types/market';

const props = defineProps<{
  assets: MediaAsset[];
}>();

const { t } = useI18n();

const activeIndex = shallowRef(0);
let touchStartX: number | undefined;
let lastWheelAt = 0;

const previewAssets = computed(() => {
  const seen = new Set<string>();
  return props.assets.filter((asset) => {
    const url = assetUrl(asset);
    if (!url || seen.has(url)) {
      return false;
    }
    seen.add(url);
    return true;
  });
});
const activeAsset = computed(() => previewAssets.value[activeIndex.value]);
const activeUrl = computed(() => (activeAsset.value ? assetUrl(activeAsset.value) : ''));
const hasMultiple = computed(() => previewAssets.value.length > 1);
const activeCaption = computed(() => {
  const asset = activeAsset.value;
  if (!asset) {
    return '';
  }
  return asset.label ?? asset.route ?? asset.viewport ?? asset.source;
});

watch(
  () => previewAssets.value.length,
  (length) => {
    if (activeIndex.value >= length) {
      activeIndex.value = Math.max(0, length - 1);
    }
  }
);

function assetUrl(asset: MediaAsset): string {
  return mediaAssetUrl(asset) || asset.url;
}

function selectPreview(index: number): void {
  const total = previewAssets.value.length;
  if (total === 0) {
    activeIndex.value = 0;
    return;
  }
  activeIndex.value = (index + total) % total;
}

function previousPreview(): void {
  selectPreview(activeIndex.value - 1);
}

function nextPreview(): void {
  selectPreview(activeIndex.value + 1);
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'ArrowLeft') {
    event.preventDefault();
    previousPreview();
    return;
  }

  if (event.key === 'ArrowRight') {
    event.preventDefault();
    nextPreview();
  }
}

function handleTouchStart(event: TouchEvent): void {
  touchStartX = event.changedTouches[0]?.clientX;
}

function handleTouchEnd(event: TouchEvent): void {
  if (touchStartX === undefined) {
    return;
  }

  const endX = event.changedTouches[0]?.clientX;
  if (endX === undefined) {
    touchStartX = undefined;
    return;
  }

  const delta = endX - touchStartX;
  touchStartX = undefined;
  if (Math.abs(delta) < 44) {
    return;
  }

  if (delta < 0) {
    nextPreview();
    return;
  }
  previousPreview();
}

function handleWheel(event: WheelEvent): void {
  if (Math.abs(event.deltaX) <= Math.abs(event.deltaY) || Math.abs(event.deltaX) < 18) {
    return;
  }

  event.preventDefault();
  const now = performance.now();
  if (now - lastWheelAt < 320) {
    return;
  }

  lastWheelAt = now;
  if (event.deltaX > 0) {
    nextPreview();
    return;
  }
  previousPreview();
}
</script>

<template>
  <section
    class="dashboard-preview"
    :class="{ 'has-thumbs': hasMultiple }"
    :aria-label="t('detail.previewsLabel')"
    tabindex="0"
    @keydown="handleKeydown"
    @touchend="handleTouchEnd"
    @touchstart.passive="handleTouchStart"
    @wheel="handleWheel"
  >
    <div v-if="hasMultiple" class="dashboard-preview__thumbs" role="listbox" :aria-label="t('detail.previewThumbs')">
      <button
        v-for="(asset, index) in previewAssets"
        :key="assetUrl(asset)"
        class="dashboard-preview__thumb"
        type="button"
        role="option"
        :aria-label="t('detail.previewSelect', { index: index + 1 })"
        :aria-selected="index === activeIndex"
        @click="selectPreview(index)"
      >
        <img :alt="asset.alt" :src="assetUrl(asset)" draggable="false" />
        <span v-if="asset.mirrorStatus === 'failed'">{{ t('detail.mediaMirrorFailed') }}</span>
      </button>
    </div>

    <div class="dashboard-preview__stage">
      <img
        v-if="activeAsset"
        :key="activeUrl"
        class="dashboard-preview__image"
        :alt="activeAsset.alt"
        :src="activeUrl"
        draggable="false"
      />
      <div v-else class="dashboard-preview__empty">
        {{ t('detail.previewEmpty') }}
      </div>

      <button
        v-if="hasMultiple"
        class="dashboard-preview__nav dashboard-preview__nav--prev"
        type="button"
        :aria-label="t('detail.previewPrevious')"
        @click="previousPreview"
      >
        ‹
      </button>
      <button
        v-if="hasMultiple"
        class="dashboard-preview__nav dashboard-preview__nav--next"
        type="button"
        :aria-label="t('detail.previewNext')"
        @click="nextPreview"
      >
        ›
      </button>

      <div v-if="activeAsset" class="dashboard-preview__caption">
        <span>{{ activeCaption }}</span>
        <span>
          {{
            t('detail.previewCount', {
              current: activeIndex + 1,
              total: previewAssets.length
            })
          }}
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.dashboard-preview {
  display: grid;
  block-size: 100%;
  min-inline-size: 0;
  min-block-size: 0;
  gap: 12px;
  outline: none;
}

.dashboard-preview.has-thumbs {
  grid-template-columns: 116px minmax(0, 1fr);
}

.dashboard-preview__stage {
  position: relative;
  overflow: hidden;
  display: grid;
  min-block-size: 0;
  block-size: 100%;
  border: 1px solid oklch(0.7 0.11 205 / 24%);
  border-radius: 12px;
  background:
    radial-gradient(circle at 20% 18%, oklch(0.64 0.13 205 / 18%), transparent 32%),
    linear-gradient(135deg, oklch(0.09 0.023 245 / 94%), oklch(0.035 0.015 255 / 96%));
  box-shadow:
    0 20px 54px oklch(0.02 0.018 255 / 36%),
    inset 0 1px 0 oklch(0.86 0.08 205 / 10%);
}

.dashboard-preview__stage::after {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background:
    linear-gradient(180deg, transparent 56%, oklch(0.025 0.014 255 / 58%) 100%),
    linear-gradient(90deg, oklch(0.06 0.018 245 / 42%), transparent 20%, transparent 80%, oklch(0.06 0.018 245 / 42%));
  content: "";
  pointer-events: none;
}

.dashboard-preview__image {
  inline-size: 100%;
  block-size: 100%;
  min-block-size: 0;
  object-fit: contain;
  user-select: none;
}

.dashboard-preview__empty {
  display: grid;
  min-block-size: 280px;
  place-items: center;
  color: oklch(0.77 0.06 210);
  font-size: 14px;
  font-weight: 720;
  letter-spacing: 0.02em;
}

.dashboard-preview__nav {
  position: absolute;
  z-index: 3;
  inset-block-start: 50%;
  display: grid;
  inline-size: 42px;
  block-size: 42px;
  place-items: center;
  border: 1px solid oklch(0.8 0.12 205 / 26%);
  border-radius: 999px;
  background: oklch(0.055 0.018 245 / 68%);
  color: oklch(0.9 0.07 205);
  cursor: pointer;
  font: inherit;
  font-size: 30px;
  font-weight: 520;
  line-height: 1;
  transform: translateY(-50%);
  backdrop-filter: blur(16px);
}

.dashboard-preview__nav:hover,
.dashboard-preview__nav:focus-visible {
  background: oklch(0.72 0.13 205);
  color: oklch(0.04 0.016 245);
}

.dashboard-preview__nav--prev {
  inset-inline-start: 14px;
}

.dashboard-preview__nav--next {
  inset-inline-end: 14px;
}

.dashboard-preview__caption {
  position: absolute;
  z-index: 3;
  inset-inline: 14px;
  inset-block-end: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: oklch(0.93 0.028 215);
  font-size: 12px;
  font-weight: 720;
  letter-spacing: 0.01em;
  pointer-events: none;
  text-shadow: 0 1px 18px oklch(0.02 0.018 255 / 80%);
}

.dashboard-preview__caption span {
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-preview__thumbs {
  display: grid;
  grid-auto-rows: 72px;
  gap: 10px;
  min-block-size: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior-block: contain;
  padding-inline-end: 4px;
  scroll-snap-type: y mandatory;
  scrollbar-color: oklch(0.7 0.13 205 / 44%) transparent;
}

.dashboard-preview__thumb {
  position: relative;
  overflow: hidden;
  inline-size: 100%;
  min-block-size: 0;
  border: 1px solid oklch(0.58 0.08 210 / 22%);
  border-radius: 8px;
  background: oklch(0.055 0.018 245);
  cursor: pointer;
  opacity: 0.66;
  padding: 0;
  scroll-snap-align: center;
  transition:
    border-color 160ms ease,
    opacity 160ms ease,
    transform 160ms ease;
}

.dashboard-preview__thumb[aria-selected="true"] {
  border-color: oklch(0.78 0.14 205 / 72%);
  box-shadow: 0 0 28px oklch(0.7 0.13 205 / 16%);
  opacity: 1;
  transform: translateY(-1px);
}

.dashboard-preview__thumb:hover,
.dashboard-preview__thumb:focus-visible {
  border-color: oklch(0.82 0.12 205 / 72%);
  opacity: 1;
}

.dashboard-preview__thumb img {
  display: block;
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
}

.dashboard-preview__thumb span {
  position: absolute;
  inset-inline: 6px;
  inset-block-end: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: oklch(0.2 0.07 30 / 82%);
  color: oklch(0.94 0.052 42);
  font-size: 10px;
  font-weight: 760;
  padding: 4px 6px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 760px) {
  .dashboard-preview,
  .dashboard-preview.has-thumbs {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(218px, 1fr) auto;
  }

  .dashboard-preview__stage,
  .dashboard-preview__image,
  .dashboard-preview__empty {
    min-block-size: 218px;
  }

  .dashboard-preview__stage {
    order: 1;
  }

  .dashboard-preview__thumbs {
    order: 2;
    display: flex;
    overflow-x: auto;
    overflow-y: hidden;
    padding-block-end: 4px;
    padding-inline-end: 0;
    scroll-snap-type: x mandatory;
  }

  .dashboard-preview__thumb {
    flex: 0 0 118px;
    aspect-ratio: 16 / 9;
    inline-size: auto;
  }

  .dashboard-preview__caption {
    inset-inline: 10px;
    inset-block-end: 10px;
  }
}

@media (max-height: 720px) {
  .dashboard-preview {
    gap: 8px;
  }

  .dashboard-preview.has-thumbs {
    grid-template-columns: 96px minmax(0, 1fr);
  }

  .dashboard-preview__stage,
  .dashboard-preview__image,
  .dashboard-preview__empty {
    min-block-size: 190px;
  }

  .dashboard-preview__thumbs {
    grid-auto-rows: 58px;
    gap: 7px;
  }

  .dashboard-preview__nav {
    inline-size: 36px;
    block-size: 36px;
    font-size: 26px;
  }

  .dashboard-preview__nav--prev {
    inset-inline-start: 10px;
  }

  .dashboard-preview__nav--next {
    inset-inline-end: 10px;
  }

  .dashboard-preview__caption {
    inset-inline: 10px;
    inset-block-end: 10px;
  }
}

@media (max-height: 560px) {
  .dashboard-preview,
  .dashboard-preview.has-thumbs {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(170px, 1fr) auto;
  }

  .dashboard-preview__stage {
    order: 1;
  }

  .dashboard-preview__thumbs {
    order: 2;
    display: flex;
    overflow-x: auto;
    overflow-y: hidden;
    padding-block-end: 4px;
    padding-inline-end: 0;
    scroll-snap-type: x mandatory;
  }

  .dashboard-preview__thumb {
    flex: 0 0 104px;
    aspect-ratio: 16 / 9;
    inline-size: auto;
  }
}
</style>
