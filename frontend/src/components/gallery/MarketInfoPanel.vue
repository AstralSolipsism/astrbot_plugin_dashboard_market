<script setup lang="ts">
import { openExternalUrl as openExternal } from '../../lib/openExternal';
import { computed } from 'vue';
import { useI18n } from '../../composables/useI18n';
import ModalShell from '../ModalShell.vue';

const repoUrl = 'https://github.com/AstralSolipsism/astrbot_dashboard_market';
const registryUrl = 'https://market.astrbot.moe/api/dashboards?installable=true';

const props = defineProps<{
  lastUpdatedAt: string;
  open: boolean;
  passed: number;
  total: number;
}>();

const emit = defineEmits<{
  close: [];
  submit: [];
}>();

const { t } = useI18n();

const lastUpdatedLabel = computed(() => formatTimestamp(props.lastUpdatedAt));
const passRate = computed(() => (props.total === 0 ? '0%' : `${Math.round((props.passed / props.total) * 100)}%`));

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}
</script>

<template>
  <ModalShell
    :aria-label="t('info.dialogLabel')"
    :close-label="t('detail.close')"
    :open="open"
    size="wide"
    @close="emit('close')"
  >
    <section class="market-info-panel">
      <header class="market-info-panel__header">
        <div>
          <span>{{ t('info.eyebrow') }}</span>
          <h2>{{ t('info.title') }}</h2>
          <p>{{ t('info.lead') }}</p>
        </div>

        <nav class="market-info-panel__actions" :aria-label="t('info.dialogLabel')">
          <button type="button" data-autofocus @click="emit('submit')">{{ t('info.submit') }}</button>
          <a :href="repoUrl" rel="noreferrer" target="_blank" @click.prevent.stop="openExternal(repoUrl)">{{ t('info.source') }}</a>
          <a :href="registryUrl" rel="noreferrer" target="_blank" @click.prevent.stop="openExternal(registryUrl)">{{ t('info.registry') }}</a>
        </nav>
      </header>

      <div class="market-info-panel__body">
        <dl class="market-info-panel__stats">
          <div>
            <dt>{{ t('info.total') }}</dt>
            <dd>{{ total }}</dd>
          </div>
          <div>
            <dt>{{ t('info.passed') }}</dt>
            <dd>{{ passed }}</dd>
          </div>
          <div>
            <dt>{{ t('info.passRate') }}</dt>
            <dd>{{ passRate }}</dd>
          </div>
          <div>
            <dt>{{ t('info.lastUpdated') }}</dt>
            <dd>{{ lastUpdatedLabel }}</dd>
          </div>
        </dl>

        <div class="market-info-panel__grid">
          <article>
            <strong>{{ t('info.useTitle') }}</strong>
            <p>{{ t('info.useBody') }}</p>
          </article>
          <article>
            <strong>{{ t('info.trustTitle') }}</strong>
            <p>{{ t('info.trustBody') }}</p>
          </article>
          <article>
            <strong>{{ t('info.publishTitle') }}</strong>
            <p>{{ t('info.publishBody') }}</p>
          </article>
        </div>

        <section class="market-info-panel__quality" :aria-label="t('info.qualityTitle')">
          <h3>{{ t('info.qualityTitle') }}</h3>
          <p>{{ t('info.qualityBody') }}</p>
        </section>
      </div>
    </section>
  </ModalShell>
</template>

<style scoped>
.market-info-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  block-size: min(720px, calc(100dvh - 36px));
  min-block-size: 0;
}

.market-info-panel__header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: start;
  padding: 22px 62px 18px 22px;
  border-block-end: 1px solid oklch(0.86 0.006 110);
  background: oklch(0.98 0.006 110);
}

.market-info-panel__header div {
  display: grid;
  min-inline-size: 0;
  gap: 9px;
}

.market-info-panel__header span {
  color: oklch(0.45 0.006 110);
  font-size: 12px;
  font-weight: 780;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.market-info-panel__header h2 {
  margin: 0;
  color: oklch(0.16 0.004 110);
  font-size: 31px;
  font-weight: 800;
  letter-spacing: 0;
  line-height: 1.08;
}

.market-info-panel__header p {
  max-inline-size: 68ch;
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.39 0.006 110);
  font-size: 14px;
  line-height: 1.5;
}

.market-info-panel__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  max-inline-size: 370px;
}

.market-info-panel__actions button,
.market-info-panel__actions a {
  display: inline-flex;
  min-block-size: 38px;
  align-items: center;
  justify-content: center;
  border: 1px solid oklch(0.18 0.004 110);
  border-radius: 999px;
  background: oklch(0.18 0.004 110);
  color: oklch(0.98 0.006 110);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 760;
  letter-spacing: 0;
  padding-inline: 15px;
  text-decoration: none;
}

.market-info-panel__actions a {
  background: oklch(0.985 0.006 110);
  color: oklch(0.17 0.004 110);
}

.market-info-panel__actions button:hover,
.market-info-panel__actions button:focus-visible,
.market-info-panel__actions a:hover,
.market-info-panel__actions a:focus-visible {
  background: oklch(0.27 0.006 110);
  color: oklch(0.98 0.006 110);
}

.market-info-panel__body {
  display: grid;
  align-content: start;
  gap: 14px;
  min-block-size: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 18px 22px 22px;
}

.market-info-panel__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  margin: 0;
  border: 1px solid oklch(0.84 0.006 110);
  border-radius: 8px;
  background: oklch(0.84 0.006 110);
}

.market-info-panel__stats div {
  display: grid;
  gap: 9px;
  min-block-size: 88px;
  background: oklch(0.985 0.006 110);
  padding: 14px;
}

.market-info-panel__stats dt {
  color: oklch(0.46 0.006 110);
  font-size: 12px;
  font-weight: 720;
}

.market-info-panel__stats dd {
  min-inline-size: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.16 0.004 110);
  font-size: 22px;
  font-weight: 780;
  letter-spacing: 0;
  line-height: 1.1;
}

.market-info-panel__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.market-info-panel__grid article,
.market-info-panel__quality {
  display: grid;
  gap: 9px;
  border: 1px solid oklch(0.84 0.006 110);
  border-radius: 8px;
  background: oklch(0.985 0.006 110);
  padding: 15px;
}

.market-info-panel__grid strong,
.market-info-panel__quality h3 {
  margin: 0;
  color: oklch(0.2 0.004 110);
  font-size: 14px;
  font-weight: 780;
  letter-spacing: 0;
}

.market-info-panel__grid p,
.market-info-panel__quality p {
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.39 0.006 110);
  font-size: 13px;
  line-height: 1.55;
}

@media (max-width: 760px) {
  .market-info-panel {
    block-size: calc(100dvh - 16px);
  }

  .market-info-panel__header {
    grid-template-columns: 1fr;
    padding: 54px 12px 14px;
  }

  .market-info-panel__actions {
    justify-content: flex-start;
    max-inline-size: none;
  }

  .market-info-panel__actions button,
  .market-info-panel__actions a {
    flex: 1 1 136px;
  }

  .market-info-panel__body {
    padding: 14px 12px 16px;
  }

  .market-info-panel__stats,
  .market-info-panel__grid {
    grid-template-columns: 1fr;
  }
}
</style>
