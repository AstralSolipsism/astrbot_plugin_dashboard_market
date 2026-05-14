<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../../composables/useI18n';

const repoUrl = 'https://github.com/AstralSolipsism/astrbot_dashboard_market';

const props = defineProps<{
  activeView: 'gallery' | 'about';
  total: number;
  passed: number;
  lastUpdatedAt: string;
}>();

const emit = defineEmits<{
  showAbout: [];
  showGallery: [];
}>();

const { languageTargetLabel, t, toggleLocale } = useI18n();

const lastUpdatedLabel = computed(() => formatTimestamp(props.lastUpdatedAt));

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}
</script>

<template>
  <header class="gallery-nav" :aria-label="t('nav.label')">
    <nav class="gallery-nav__pill">
      <button :data-active="activeView === 'gallery'" type="button" @click="emit('showGallery')">
        {{ t('nav.index') }}
      </button>
      <button :data-active="activeView === 'about'" type="button" @click="emit('showAbout')">
        {{ t('nav.info') }}
      </button>
      <span>{{ t('nav.collected', { total }) }}</span>
      <span>{{ t('nav.available', { passed }) }}</span>
      <span class="gallery-nav__updated">{{ t('nav.lastUpdated', { date: lastUpdatedLabel }) }}</span>
      <button class="gallery-nav__locale" type="button" :aria-label="t('nav.switchLanguage')" @click="toggleLocale">
        {{ languageTargetLabel }}
      </button>
    </nav>
    <a class="gallery-nav__github" :aria-label="t('nav.githubRepo')" :href="repoUrl" rel="noreferrer" target="_blank">
      <svg aria-hidden="true" class="gallery-nav__github-icon" viewBox="0 0 24 24">
        <path
          clip-rule="evenodd"
          d="M12 2C6.477 2 2 6.484 2 12.021c0 4.428 2.865 8.184 6.839 9.504.5.092.682-.217.682-.482 0-.237-.009-.866-.014-1.7-2.782.605-3.369-1.344-3.369-1.344-.455-1.158-1.11-1.466-1.11-1.466-.908-.622.069-.609.069-.609 1.004.071 1.532 1.034 1.532 1.034.892 1.532 2.341 1.09 2.91.833.091-.647.35-1.09.636-1.341-2.221-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.03-2.688-.103-.254-.446-1.274.098-2.656 0 0 .84-.27 2.75 1.026A9.55 9.55 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.026 2.747-1.026.546 1.382.203 2.402.1 2.656.64.7 1.028 1.595 1.028 2.688 0 3.847-2.337 4.695-4.566 4.944.359.31.678.923.678 1.86 0 1.343-.012 2.426-.012 2.756 0 .267.18.578.688.48A10.024 10.024 0 0 0 22 12.021C22 6.484 17.523 2 12 2Z"
          fill-rule="evenodd"
        />
      </svg>
    </a>
  </header>
</template>

<style scoped>
.gallery-nav {
  position: fixed;
  z-index: 40;
  inset-block-start: 22px;
  inset-inline: 24px;
  display: flex;
  align-items: start;
  justify-content: space-between;
  pointer-events: none;
}

.gallery-nav__pill,
.gallery-nav__github {
  pointer-events: auto;
  border: 1px solid oklch(0.82 0.006 110 / 68%);
  background: oklch(0.98 0.006 110 / 78%);
  color: oklch(0.16 0.004 110);
  box-shadow: 0 18px 48px oklch(0.18 0.006 110 / 10%);
  backdrop-filter: blur(18px);
}

.gallery-nav__pill {
  display: flex;
  max-inline-size: calc(100vw - 160px);
  min-block-size: 46px;
  align-items: center;
  gap: 4px;
  overflow-x: auto;
  border-radius: 999px;
  padding: 5px;
  scrollbar-width: none;
}

.gallery-nav__pill::-webkit-scrollbar {
  display: none;
}

.gallery-nav__pill button,
.gallery-nav__pill span,
.gallery-nav__locale,
.gallery-nav__github {
  display: inline-flex;
  min-block-size: 36px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  color: inherit;
  font-size: 13px;
  font-weight: 650;
  letter-spacing: 0;
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;
}

.gallery-nav__pill button {
  border: 0;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  padding-inline: 15px;
  transition:
    background-color 160ms ease,
    color 160ms ease;
}

.gallery-nav__pill button[data-active="true"] {
  background: oklch(0.17 0.004 110);
  color: oklch(0.97 0.006 110);
}

.gallery-nav__locale {
  border: 0;
  background: transparent;
  cursor: pointer;
  padding-inline: 14px;
}

.gallery-nav__pill button:hover,
.gallery-nav__pill button:focus-visible,
.gallery-nav__locale:hover,
.gallery-nav__locale:focus-visible {
  background: oklch(0.17 0.004 110);
  color: oklch(0.97 0.006 110);
}

.gallery-nav__pill span {
  padding-inline: 12px;
  color: oklch(0.45 0.005 110);
}

.gallery-nav__updated {
  color: oklch(0.34 0.006 110) !important;
  font-variant-numeric: tabular-nums;
}

.gallery-nav__github {
  inline-size: 46px;
  block-size: 46px;
  padding: 0;
  transition:
    transform 180ms cubic-bezier(0.22, 1, 0.36, 1),
    background-color 180ms ease,
    color 180ms ease;
}

.gallery-nav__github:hover,
.gallery-nav__github:focus-visible {
  transform: translateY(-1px);
  background: oklch(0.17 0.004 110);
  color: oklch(0.97 0.006 110);
}

.gallery-nav__github-icon {
  inline-size: 21px;
  block-size: 21px;
  fill: currentColor;
}

@media (max-width: 700px) {
  .gallery-nav {
    inset-block-start: 14px;
    inset-inline: 12px;
  }

  .gallery-nav__pill {
    max-inline-size: calc(100vw - 126px);
  }

  .gallery-nav__pill span {
    display: none;
  }

  .gallery-nav__updated {
    display: inline-flex !important;
  }

  .gallery-nav__github {
    inline-size: 46px;
  }
}
</style>
