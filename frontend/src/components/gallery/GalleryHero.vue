<script setup lang="ts">
import { useI18n } from '../../composables/useI18n';

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
  </section>
</template>

<style scoped>
.gallery-hero {
  position: absolute;
  inset-block-start: 0;
  inset-inline-start: 0;
  z-index: 2;
  display: flex;
  inline-size: min(var(--gallery-grid-x, 480px), 480px);
  block-size: var(--gallery-card-height, 260px);
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding-inline: 28px;
  transform: translate(-50%, -50%);
  color: oklch(0.98 0.018 220);
  pointer-events: none;
  text-align: center;
  text-shadow:
    0 2px 18px oklch(0.02 0.02 260 / 72%),
    0 0 42px oklch(0.74 0.14 210 / 18%);
  user-select: none;
}

.gallery-hero__eyebrow {
  margin: 0;
  color: oklch(0.82 0.11 207);
  font-size: 11px;
  font-weight: 820;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  white-space: nowrap;
}

.gallery-hero h1 {
  max-inline-size: 424px;
  margin: 0;
  font-size: clamp(38px, 4.1vw, 50px);
  font-weight: 860;
  letter-spacing: -0.055em;
  line-height: 0.94;
  text-wrap: balance;
}

.gallery-hero__lead {
  max-inline-size: 360px;
  margin: 0;
  color: oklch(0.91 0.022 218 / 88%);
  font-size: 13px;
  font-weight: 620;
  letter-spacing: -0.01em;
  line-height: 1.52;
  text-wrap: pretty;
}

.gallery-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  justify-content: center;
  margin-block-start: 2px;
  pointer-events: auto;
}

.gallery-hero__actions button {
  display: inline-flex;
  min-block-size: 28px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-block-end: 1px solid currentColor;
  background: transparent;
  color: oklch(0.84 0.12 205);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 820;
  letter-spacing: 0.04em;
  line-height: 1.15;
  padding: 0 0 3px;
  text-transform: uppercase;
  transition:
    transform 180ms cubic-bezier(0.22, 1, 0.36, 1),
    color 180ms ease;
}

.gallery-hero__actions button:hover,
.gallery-hero__actions button:focus-visible {
  color: oklch(0.98 0.02 220);
  outline: none;
  transform: translateY(-2px);
}

@media (max-width: 720px) {
  .gallery-hero {
    inline-size: min(var(--gallery-grid-x, 480px), 480px);
    gap: 11px;
    padding-inline: 34px;
  }

  .gallery-hero h1 {
    font-size: 38px;
  }

  .gallery-hero__lead {
    max-inline-size: 340px;
    font-size: 14px;
  }
}
</style>
