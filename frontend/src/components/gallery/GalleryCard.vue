<script setup lang="ts">
import { openExternalUrl as openExternal } from '../../lib/openExternal';
import { computed, onBeforeUnmount, onMounted, shallowRef, useTemplateRef, watch } from 'vue';
import { useI18n } from '../../composables/useI18n';
import type { GalleryItem } from '../../types/gallery';
import BalatroBackdrop from './BalatroBackdrop.vue';

const props = defineProps<{
  item: GalleryItem;
}>();

const emit = defineEmits<{
  select: [item: GalleryItem];
}>();

const { t } = useI18n();
const cardRef = useTemplateRef<HTMLElement>('card');
const imageFailed = shallowRef(false);
const imageLoaded = shallowRef(false);
const isInteracting = shallowRef(false);
const isNearViewport = shallowRef(false);
const revealDone = shallowRef(false);
const revealProgress = shallowRef(0);

let intersectionObserver: IntersectionObserver | undefined;
let revealFrameId = 0;
let revealTimeoutId = 0;

const revealDurationMs = 2760;
const revealDoneDelayMs = 2800;

const installBadgeLabel = computed(() => {
  switch (props.item.installState) {
    case 'current':
      return t('install.stateCurrent');
    case 'installed':
      return t('install.stateInstalled');
    case 'restartRequired':
      return t('install.stateRestartRequired');
    default:
      return '';
  }
});

const showImage = computed(() => Boolean(props.item.imageUrl) && imageLoaded.value && !imageFailed.value);
const balatroPalette = {
  color1: '#06b6d4',
  color2: '#b8b096',
  color3: '#000000'
};
const balatroVisible = computed(() => !showImage.value || !revealDone.value);
const balatroActive = computed(() => balatroVisible.value && (isNearViewport.value || isInteracting.value));
const imageRevealStyle = computed<Record<string, string>>(() => {
  const clipPath = imageClipPath.value;
  return {
    clipPath,
    WebkitClipPath: clipPath
  };
});
const imageClipPath = computed(() => {
  if (!showImage.value) {
    return 'polygon(50% 50%, 50% 50%, 50% 50%)';
  }
  return createSpiralClipPath(revealProgress.value);
});

watch(
  () => props.item.imageUrl,
  () => resetImageState()
);

onMounted(() => {
  const card = cardRef.value;
  if (!card || typeof IntersectionObserver === 'undefined') {
    isNearViewport.value = true;
    return;
  }
  intersectionObserver = new IntersectionObserver(
    (entries) => {
      isNearViewport.value = entries.some((entry) => entry.isIntersecting);
    },
    { root: null, rootMargin: '960px' }
  );
  intersectionObserver.observe(card);
});

onBeforeUnmount(() => {
  intersectionObserver?.disconnect();
  cancelRevealTimers();
});

function selectItem(): void {
  emit('select', props.item);
}

function handleImageLoad(): void {
  imageLoaded.value = true;
  imageFailed.value = false;
  revealProgress.value = 0;
  revealDone.value = false;
  cancelRevealTimers();
  if (prefersReducedMotion()) {
    revealProgress.value = 1;
    revealDone.value = true;
    return;
  }
  const startedAt = performance.now();
  const updateReveal = (time: number) => {
    const rawProgress = clamp((time - startedAt) / revealDurationMs, 0, 1);
    revealProgress.value = easeInOutCubic(rawProgress);
    if (rawProgress < 1) {
      revealFrameId = requestAnimationFrame(updateReveal);
      return;
    }
    revealProgress.value = 1;
    revealFrameId = 0;
  };
  revealFrameId = requestAnimationFrame((time) => {
    updateReveal(time);
    revealTimeoutId = window.setTimeout(() => {
      if (revealFrameId) {
        cancelAnimationFrame(revealFrameId);
        revealFrameId = 0;
      }
      revealProgress.value = 1;
      revealDone.value = true;
      revealTimeoutId = 0;
    }, revealDoneDelayMs);
  });
}

function handleImageError(): void {
  resetImageState();
  imageFailed.value = true;
}

function resetImageState(): void {
  cancelRevealTimers();
  imageFailed.value = false;
  imageLoaded.value = false;
  revealProgress.value = 0;
  revealDone.value = false;
}

function cancelRevealTimers(): void {
  if (revealFrameId) {
    cancelAnimationFrame(revealFrameId);
    revealFrameId = 0;
  }
  if (revealTimeoutId) {
    window.clearTimeout(revealTimeoutId);
    revealTimeoutId = 0;
  }
}

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function createSpiralClipPath(progress: number): string {
  const p = clamp(progress, 0, 1);
  if (p >= 0.985) {
    return 'inset(0)';
  }

  const points: string[] = [];
  const steps = 112;
  const maxRadius = 92;
  const baseRadius = Math.pow(p, 0.72) * maxRadius;
  const swirlPhase = p * Math.PI * 4.6;
  const turbulence = Math.max(0.08, 1 - p) * 0.18;

  for (let index = 0; index <= steps; index += 1) {
    const turn = index / steps;
    const angle = -Math.PI / 2 + turn * Math.PI * 2;
    const swirl =
      Math.sin(angle * 2.35 - swirlPhase) * turbulence +
      Math.sin(angle * 5.15 + swirlPhase * 0.62) * turbulence * 0.42;
    const leadingArm = Math.sin((turn - p * 1.25) * Math.PI * 2) * (1 - p) * 0.1;
    const radius = baseRadius * clamp(1 + swirl + leadingArm, 0.16, 1.18);
    const x = 50 + Math.cos(angle + (1 - p) * 0.72) * radius;
    const y = 50 + Math.sin(angle + (1 - p) * 0.72) * radius;
    points.push(`${x.toFixed(2)}% ${y.toFixed(2)}%`);
  }

  return `polygon(${points.join(', ')})`;
}

function easeInOutCubic(value: number): number {
  return value < 0.5 ? 4 * value * value * value : 1 - Math.pow(-2 * value + 2, 3) / 2;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
</script>

<template>
  <article
    ref="card"
    class="gallery-card"
    role="button"
    tabindex="0"
    :aria-label="item.title"
    @blur.capture="isInteracting = false"
    @click="selectItem"
    @focus.capture="isInteracting = true"
    @keydown.enter.prevent="selectItem"
    @keydown.space.prevent="selectItem"
    @pointerenter="isInteracting = true"
    @pointerleave="isInteracting = false"
  >
    <BalatroBackdrop
      class="gallery-card__backdrop"
      :active="balatroActive"
      :color1="balatroPalette.color1"
      :color2="balatroPalette.color2"
      :color3="balatroPalette.color3"
      :seed="item.visualSeed"
    />
    <img
      v-if="item.imageUrl && !imageFailed"
      class="gallery-card__image"
      :class="{ 'is-loaded': showImage }"
      :alt="item.title"
      :src="item.imageUrl"
      :style="imageRevealStyle"
      draggable="false"
      @error="handleImageError"
      @load="handleImageLoad"
    />
    <div class="gallery-card__shade" aria-hidden="true"></div>
    <span v-if="installBadgeLabel" class="gallery-card__state" :data-state="item.installState">
      {{ installBadgeLabel }}
    </span>
    <div class="gallery-card__meta">
      <a
        class="gallery-card__author"
        :aria-label="t('card.authorRepository', { author: item.authorId })"
        :href="item.repositoryUrl"
        rel="noreferrer"
        target="_blank"
        data-no-pan="true"
        @click.prevent.stop="openExternal(item.repositoryUrl)"
        @keydown.stop
      >
        {{ item.authorId }}
      </a>
      <button
        class="gallery-card__open"
        type="button"
        data-no-pan="true"
        @click.stop="selectItem"
        @keydown.stop
      >
        {{ t('card.open') }}
      </button>
    </div>
    <span v-if="item.previewFailed" class="gallery-card__warning">{{ t('card.previewMirrorFailed') }}</span>
  </article>
</template>

<style scoped>
.gallery-card {
  position: relative;
  overflow: hidden;
  inline-size: var(--gallery-card-width, 416px);
  block-size: var(--gallery-card-height, 260px);
  border: 1px solid oklch(0.68 0.065 220 / 24%);
  border-radius: var(--gallery-card-radius, 8px);
  background: oklch(0.08 0.018 245 / 72%);
  box-shadow:
    0 16px 38px oklch(0.02 0.018 255 / 34%),
    inset 0 1px 0 oklch(0.86 0.06 210 / 12%);
  cursor: pointer;
  outline: none;
  transform-origin: center;
  transition:
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 220ms ease,
    border-color 220ms ease;
}

.gallery-card:hover,
.gallery-card:focus-visible {
  z-index: 5;
  border-color: oklch(0.78 0.11 205 / 42%);
  box-shadow:
    0 22px 60px oklch(0.02 0.018 255 / 44%),
    0 0 42px oklch(0.72 0.12 205 / 12%),
    inset 0 1px 0 oklch(0.88 0.08 205 / 18%);
  transform: scale(var(--gallery-card-hover-scale, 1.1));
}

.gallery-card__image {
  position: absolute;
  z-index: 2;
  inset: 0;
  display: block;
  inline-size: 100%;
  block-size: 100%;
  border-radius: inherit;
  object-fit: cover;
  opacity: 0;
  transition: opacity 80ms ease;
  user-select: none;
  will-change: clip-path;
}

.gallery-card__image.is-loaded {
  opacity: 1;
}

.gallery-card__backdrop {
  z-index: 1;
}

.gallery-card__shade {
  position: absolute;
  z-index: 3;
  inset: 0;
  border-radius: inherit;
  background:
    linear-gradient(180deg, oklch(0.12 0.005 110 / 0%) 44%, oklch(0.12 0.005 110 / 42%) 100%),
    linear-gradient(0deg, oklch(0.95 0.006 110 / 8%), oklch(0.95 0.006 110 / 8%));
  opacity: 0;
  transition: opacity 200ms ease;
}

.gallery-card:hover .gallery-card__shade,
.gallery-card:focus-visible .gallery-card__shade {
  opacity: 1;
}

.gallery-card__meta {
  position: absolute;
  z-index: 5;
  inset-inline: var(--gallery-card-inset, 14px);
  inset-block-end: var(--gallery-card-inset, 14px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--gallery-card-meta-gap, 10px);
  pointer-events: none;
}

.gallery-card__state,
.gallery-card__warning {
  position: absolute;
  z-index: 6;
  inset-block-start: var(--gallery-card-inset, 14px);
  display: inline-flex;
  max-inline-size: var(--gallery-card-badge-max-width, 178px);
  min-block-size: var(--gallery-card-badge-height, 30px);
  align-items: center;
  border-radius: 999px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  backdrop-filter: blur(14px);
}

.gallery-card__state {
  inset-inline-start: var(--gallery-card-inset, 14px);
  background: oklch(0.18 0.004 110 / 88%);
  color: oklch(0.98 0.006 110);
  font-size: var(--gallery-card-font-size, 12px);
  font-weight: 760;
  letter-spacing: 0;
  padding-inline: clamp(8px, var(--gallery-card-inset, 14px), 11px);
}

.gallery-card__state[data-state="current"] {
  background: oklch(0.9 0.055 150 / 92%);
  color: oklch(0.27 0.08 150);
}

.gallery-card__state[data-state="restartRequired"] {
  background: oklch(0.94 0.052 78 / 94%);
  color: oklch(0.34 0.07 70);
}

.gallery-card__warning {
  inset-inline-end: var(--gallery-card-inset, 14px);
  background: oklch(0.96 0.04 32 / 88%);
  color: oklch(0.38 0.09 28);
  font-size: var(--gallery-card-font-size, 12px);
  font-weight: 730;
  letter-spacing: 0;
  padding-inline: clamp(8px, var(--gallery-card-inset, 14px), 11px);
}

.gallery-card__author,
.gallery-card__open {
  display: inline-flex;
  min-block-size: var(--gallery-card-control-height, 34px);
  align-items: center;
  border-radius: 999px;
  background: oklch(0.98 0.006 110 / 88%);
  color: oklch(0.15 0.004 110);
  font-size: var(--gallery-card-font-size, 12px);
  font-weight: 720;
  letter-spacing: 0;
  line-height: 1;
  white-space: nowrap;
  backdrop-filter: blur(14px);
}

.gallery-card__author {
  min-inline-size: 0;
  max-inline-size: min(220px, calc(var(--gallery-card-width, 416px) - 112px));
  overflow: hidden;
  opacity: 0;
  padding-inline: clamp(9px, var(--gallery-card-inset, 14px), 13px);
  text-overflow: ellipsis;
  text-decoration: none;
  transform: translateY(8px);
  transition:
    background-color 160ms ease,
    color 160ms ease,
    opacity 180ms ease,
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1);
}

.gallery-card__open {
  flex: 0 0 auto;
  border: 0;
  opacity: 0;
  padding-inline: clamp(9px, var(--gallery-card-inset, 14px), 13px);
  transform: translateY(8px);
  transition:
    background-color 160ms ease,
    color 160ms ease,
    opacity 180ms ease,
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1);
}

.gallery-card:hover .gallery-card__meta,
.gallery-card:focus-within .gallery-card__meta {
  pointer-events: auto;
}

.gallery-card:hover .gallery-card__author,
.gallery-card:focus-within .gallery-card__author,
.gallery-card:hover .gallery-card__open,
.gallery-card:focus-within .gallery-card__open {
  opacity: 1;
  transform: translateY(0);
}

.gallery-card__author:hover,
.gallery-card__author:focus-visible,
.gallery-card__open:hover,
.gallery-card__open:focus-visible {
  background: oklch(0.16 0.004 110);
  color: oklch(0.97 0.006 110);
}

.gallery-card__open {
  cursor: pointer;
  font-family: inherit;
}

@media (max-width: 720px) {
  .gallery-card {
    inline-size: var(--gallery-card-width, 416px);
    block-size: var(--gallery-card-height, 260px);
  }

  .gallery-card__meta {
    pointer-events: auto;
  }

  .gallery-card__author,
  .gallery-card__open {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .gallery-card__image {
    transition: none;
  }

  .gallery-card__image.is-revealed {
    clip-path: none;
  }
}
</style>
