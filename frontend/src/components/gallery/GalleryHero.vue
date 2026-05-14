<script setup lang="ts">
import { useI18n } from '../../composables/useI18n';

defineProps<{
  loading: boolean;
  total: number;
  passed: number;
}>();

const emit = defineEmits<{
  browse: [];
  submit: [];
}>();

const { t } = useI18n();
</script>

<template>
  <section class="gallery-hero" aria-labelledby="gallery-title">
    <p class="gallery-hero__eyebrow">{{ t('hero.eyebrow') }}</p>
    <h1 id="gallery-title">{{ t('hero.title') }}</h1>
    <p class="gallery-hero__lead">
      {{ t('hero.lead') }}
    </p>
    <div class="gallery-hero__actions" data-no-pan="true">
      <button type="button" @click="emit('browse')">{{ t('hero.openIndex') }}</button>
      <button type="button" @click="emit('submit')">
        {{ t('hero.submitWork') }}
      </button>
    </div>
    <p class="gallery-hero__meta">
      <span v-if="loading">{{ t('hero.loading') }}</span>
      <span v-else>{{ t('hero.stats', { total, passed }) }}</span>
    </p>
  </section>
</template>

<style scoped>
.gallery-hero {
  position: absolute;
  inset-block-start: 0;
  inset-inline-start: 0;
  display: grid;
  z-index: 2;
  inline-size: var(--gallery-card-width, 416px);
  block-size: var(--gallery-card-height, 260px);
  grid-template-columns: 145px minmax(0, 1fr);
  grid-template-rows: 1fr auto;
  align-content: stretch;
  column-gap: 18px;
  row-gap: 16px;
  justify-items: stretch;
  padding: 22px;
  border: 1px solid oklch(0.84 0.006 110 / 76%);
  border-radius: 8px;
  background:
    radial-gradient(circle at 50% 0%, oklch(0.99 0.018 92 / 54%), transparent 60%),
    linear-gradient(180deg, oklch(0.99 0.004 110 / 76%), oklch(0.97 0.006 110 / 64%));
  box-shadow:
    0 14px 42px oklch(0.18 0.006 110 / 8%),
    inset 0 1px 0 oklch(1 0 0 / 68%);
  transform: translate(-50%, -50%);
  backdrop-filter: blur(8px);
  color: oklch(0.15 0.004 110);
  text-align: left;
  user-select: none;
}

.gallery-hero__eyebrow {
  grid-column: 1;
  grid-row: 1;
  align-self: start;
  margin: 0;
  color: oklch(0.42 0.006 110);
  font-size: 10px;
  font-weight: 760;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.gallery-hero h1 {
  grid-column: 2;
  grid-row: 1;
  align-self: end;
  max-inline-size: 220px;
  margin: 0;
  font-size: 37px;
  font-weight: 820;
  letter-spacing: -0.045em;
  line-height: 0.95;
  text-wrap: balance;
}

.gallery-hero__lead {
  grid-column: 1;
  grid-row: 1;
  align-self: center;
  max-inline-size: 136px;
  margin: 18px 0 0;
  color: oklch(0.38 0.006 110);
  font-size: 12px;
  font-weight: 540;
  line-height: 1.5;
  text-wrap: pretty;
}

.gallery-hero__actions {
  display: flex;
  flex-wrap: wrap;
  grid-column: 2;
  grid-row: 2;
  gap: 6px;
  justify-content: end;
  margin-block-start: 0;
}

.gallery-hero__actions button {
  display: inline-flex;
  min-block-size: 32px;
  align-items: center;
  justify-content: center;
  border: 1px solid oklch(0.18 0.004 110);
  border-radius: 999px;
  background: oklch(0.17 0.004 110);
  color: oklch(0.97 0.006 110);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0;
  line-height: 1;
  padding-inline: 13px;
  transition:
    transform 180ms cubic-bezier(0.22, 1, 0.36, 1),
    background-color 180ms ease,
    color 180ms ease;
}

.gallery-hero__actions button + button {
  background: oklch(0.98 0.006 110);
  color: oklch(0.17 0.004 110);
}

.gallery-hero__actions button:hover,
.gallery-hero__actions button:focus-visible {
  transform: translateY(-2px);
}

.gallery-hero__meta {
  grid-column: 1;
  grid-row: 2;
  align-self: center;
  justify-self: start;
  margin: 0;
  color: oklch(0.53 0.005 110);
  font-size: 11px;
  font-weight: 680;
  letter-spacing: 0;
}

.gallery-hero__actions,
.gallery-hero__meta {
  align-self: end;
}

@media (max-width: 720px) {
  .gallery-hero {
    inline-size: var(--gallery-card-width, 416px);
    block-size: var(--gallery-card-height, 260px);
    padding: 20px;
  }

  .gallery-hero h1 {
    font-size: 34px;
  }
}
</style>
