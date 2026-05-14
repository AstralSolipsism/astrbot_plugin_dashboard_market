<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../../composables/useI18n';
import type { GalleryItem } from '../../types/gallery';

const props = defineProps<{
  item: GalleryItem;
}>();

const emit = defineEmits<{
  select: [item: GalleryItem];
}>();

const { t } = useI18n();

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

function selectItem(): void {
  emit('select', props.item);
}
</script>

<template>
  <article
    class="gallery-card"
    role="button"
    tabindex="0"
    :aria-label="item.title"
    @click="selectItem"
    @keydown.enter.prevent="selectItem"
    @keydown.space.prevent="selectItem"
  >
    <img class="gallery-card__image" :alt="item.title" :src="item.imageUrl" draggable="false" />
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
        @click.stop
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
  border: 1px solid oklch(0.86 0.006 110);
  border-radius: 8px;
  background: oklch(0.94 0.006 110);
  box-shadow: 0 12px 32px oklch(0.18 0.006 110 / 6%);
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
  border-color: oklch(0.22 0.004 110);
  box-shadow: 0 24px 58px oklch(0.16 0.006 110 / 14%);
  transform: scale(1.1);
}

.gallery-card__image {
  display: block;
  inline-size: 100%;
  block-size: 100%;
  border-radius: inherit;
  object-fit: cover;
  user-select: none;
}

.gallery-card__shade {
  position: absolute;
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
  inset-inline: 14px;
  inset-block-end: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  pointer-events: none;
}

.gallery-card__state,
.gallery-card__warning {
  position: absolute;
  inset-block-start: 14px;
  display: inline-flex;
  max-inline-size: 178px;
  min-block-size: 30px;
  align-items: center;
  border-radius: 999px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  backdrop-filter: blur(14px);
}

.gallery-card__state {
  inset-inline-start: 14px;
  background: oklch(0.18 0.004 110 / 88%);
  color: oklch(0.98 0.006 110);
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0;
  padding-inline: 11px;
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
  inset-inline-end: 14px;
  background: oklch(0.96 0.04 32 / 88%);
  color: oklch(0.38 0.09 28);
  font-size: 12px;
  font-weight: 730;
  letter-spacing: 0;
  padding-inline: 11px;
}

.gallery-card__author,
.gallery-card__open {
  display: inline-flex;
  min-block-size: 34px;
  align-items: center;
  border-radius: 999px;
  background: oklch(0.98 0.006 110 / 88%);
  color: oklch(0.15 0.004 110);
  font-size: 12px;
  font-weight: 720;
  letter-spacing: 0;
  line-height: 1;
  white-space: nowrap;
  backdrop-filter: blur(14px);
}

.gallery-card__author {
  min-inline-size: 0;
  max-inline-size: 220px;
  overflow: hidden;
  opacity: 0;
  padding-inline: 13px;
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
  padding-inline: 13px;
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
</style>
