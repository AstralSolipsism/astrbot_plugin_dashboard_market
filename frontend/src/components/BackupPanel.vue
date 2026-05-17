<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../composables/useI18n';
import { resolveRuntimeInstallState } from '../lib/installState';
import type { DashboardInstallDisplayState, PluginBackup, PluginDashboardStatus } from '../types/market';
import ModalShell from './ModalShell.vue';

const props = defineProps<{
  open: boolean;
  restoringBackupId: string;
  status: PluginDashboardStatus | undefined;
}>();

const emit = defineEmits<{
  close: [];
  restore: [backup: PluginBackup];
}>();

const { t } = useI18n();

const installedLabel = computed(() => {
  const dashboard = props.status?.installed?.dashboard;
  return dashboard ? `${dashboard.id}@${dashboard.version}` : t('install.noInstalled');
});
const distLabel = computed(() => props.status?.dist.version ?? t('install.unknownVersion'));
const runtimePath = computed(() => props.status?.runtime.dashboardPath ?? t('install.unknownVersion'));
const runtimeState = computed(() => resolveRuntimeInstallState(props.status));
const runtimeStateLabel = computed(() => labelForInstallState(runtimeState.value));
const runtimeMessage = computed(() => {
  if (!props.status) {
    return t('install.unknownVersion');
  }
  if (props.status.runtime.requiresRestart) {
    return t('install.restartRequired');
  }
  if (props.status.runtime.usesDataDist) {
    return t('install.runtimeReady');
  }
  return t('install.runtimeCustom');
});
const distStatus = computed(() => {
  if (!props.status) {
    return t('install.unknownVersion');
  }
  return props.status.dist.exists ? t('install.distExists') : t('install.distMissing');
});
const backups = computed(() => props.status?.backups ?? []);

function formatTimestamp(value: string | undefined): string {
  if (!value) {
    return t('install.unknownTime');
  }
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

function backupLabel(backup: PluginBackup): string {
  return backup.sourceVersion || backup.id;
}

function labelForInstallState(state: DashboardInstallDisplayState): string {
  switch (state) {
    case 'current':
      return t('install.stateCurrent');
    case 'installed':
      return t('install.stateInstalled');
    case 'restartRequired':
      return t('install.stateRestartRequired');
    default:
      return t('install.stateNone');
  }
}
</script>

<template>
  <ModalShell
    :aria-label="t('install.panelTitle')"
    :close-label="t('install.panelClose')"
    :open="open"
    size="medium"
    @close="emit('close')"
  >
    <section class="install-manager">
      <header class="install-manager__header">
        <div>
          <span>{{ t('install.runtimeTitle') }}</span>
          <h2>{{ installedLabel }}</h2>
          <p>{{ runtimeMessage }}</p>
        </div>
        <strong class="install-manager__state" :data-state="runtimeState">{{ runtimeStateLabel }}</strong>
      </header>

      <dl class="install-manager__summary">
        <div>
          <dt>{{ t('install.currentDist') }}</dt>
          <dd>{{ distLabel }}</dd>
          <span>{{ distStatus }}</span>
        </div>
        <div>
          <dt>{{ t('install.runtime') }}</dt>
          <dd>{{ runtimePath }}</dd>
          <span>{{ runtimeMessage }}</span>
        </div>
        <div>
          <dt>{{ t('install.astrbotVersion') }}</dt>
          <dd>{{ status?.astrbotVersion ?? t('install.unknownVersion') }}</dd>
        </div>
        <div>
          <dt>{{ t('install.backups') }}</dt>
          <dd>{{ backups.length }}</dd>
          <span>{{ t('install.backupCount', { total: backups.length }) }}</span>
        </div>
      </dl>

      <section class="install-manager__backups" :aria-label="t('install.backups')">
        <div class="install-manager__section-header">
          <h3>{{ t('install.backups') }}</h3>
          <span>{{ t('install.backupCount', { total: backups.length }) }}</span>
        </div>

        <p v-if="backups.length === 0" class="install-manager__empty">
          {{ t('install.noBackups') }}
        </p>
        <div v-else class="install-manager__backup-list">
          <article v-for="backup in backups" :key="backup.id" class="install-manager__backup">
            <div>
              <strong>{{ backupLabel(backup) }}</strong>
              <span>{{ formatTimestamp(backup.createdAt) }}</span>
            </div>
            <button type="button" :disabled="Boolean(restoringBackupId)" @click="emit('restore', backup)">
              {{ restoringBackupId === backup.id ? t('install.restoring') : t('install.restore') }}
            </button>
          </article>
        </div>
      </section>
    </section>
  </ModalShell>
</template>

<style scoped>
.install-manager {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  block-size: min(680px, calc(100dvh - 36px));
  min-block-size: 0;
}

.install-manager__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 62px 16px 18px;
  border-block-end: 1px solid oklch(0.86 0.006 110);
  background: oklch(0.98 0.006 110);
}

.install-manager__header div {
  display: grid;
  min-inline-size: 0;
  gap: 7px;
}

.install-manager__header span,
.install-manager__summary dt,
.install-manager__summary span,
.install-manager__section-header span,
.install-manager__backup span,
.install-manager__empty {
  color: oklch(0.45 0.006 110);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.install-manager__header h2 {
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.16 0.004 110);
  font-size: 24px;
  font-weight: 780;
  letter-spacing: 0;
  line-height: 1.14;
}

.install-manager__header p,
.install-manager__empty {
  margin: 0;
  overflow-wrap: anywhere;
}

.install-manager__state {
  display: inline-flex;
  flex: 0 0 auto;
  max-inline-size: 180px;
  min-block-size: 30px;
  align-items: center;
  border-radius: 999px;
  overflow: hidden;
  background: oklch(0.91 0.006 110);
  color: oklch(0.36 0.006 110);
  font-size: 12px;
  font-weight: 780;
  letter-spacing: 0;
  padding-inline: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.install-manager__state[data-state="current"] {
  background: oklch(0.9 0.055 150);
  color: oklch(0.27 0.08 150);
}

.install-manager__state[data-state="restartRequired"] {
  background: oklch(0.94 0.052 78);
  color: oklch(0.34 0.07 70);
}

.install-manager__summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  margin: 0;
  border-block-end: 1px solid oklch(0.84 0.006 110);
  background: oklch(0.84 0.006 110);
}

.install-manager__summary div {
  display: grid;
  gap: 7px;
  min-block-size: 96px;
  background: oklch(0.985 0.006 110);
  padding: 13px 14px;
}

.install-manager__summary dd {
  min-inline-size: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.18 0.004 110);
  font-size: 14px;
  font-weight: 760;
  line-height: 1.35;
}

.install-manager__backups {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-block-size: 0;
  gap: 10px;
  overflow: hidden;
  padding: 16px 18px 18px;
}

.install-manager__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.install-manager__section-header h3 {
  margin: 0;
  color: oklch(0.22 0.004 110);
  font-size: 14px;
  font-weight: 780;
  letter-spacing: 0;
}

.install-manager__backup-list {
  display: grid;
  align-content: start;
  gap: 8px;
  min-block-size: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.install-manager__backup {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid oklch(0.84 0.006 110);
  border-radius: 8px;
  background: oklch(0.985 0.006 110);
  padding: 12px;
}

.install-manager__backup div {
  display: grid;
  min-inline-size: 0;
  gap: 5px;
}

.install-manager__backup strong {
  overflow-wrap: anywhere;
  color: oklch(0.18 0.004 110);
  font-size: 13px;
  font-weight: 760;
  letter-spacing: 0;
}

.install-manager__backup button {
  display: inline-flex;
  flex: 0 0 auto;
  min-block-size: 36px;
  align-items: center;
  border: 1px solid oklch(0.2 0.026 184);
  border-radius: 999px;
  background: oklch(0.2 0.026 184);
  color: white;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 760;
  letter-spacing: 0;
  padding-inline: 14px;
}

.install-manager__backup button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

@media (max-width: 620px) {
  .install-manager {
    block-size: calc(100dvh - 16px);
  }

  .install-manager__header {
    align-items: stretch;
    flex-direction: column;
    padding: 54px 12px 14px;
  }

  .install-manager__state {
    align-self: flex-start;
  }

  .install-manager__summary {
    grid-template-columns: 1fr;
  }

  .install-manager__backups {
    padding: 14px 12px 16px;
  }

  .install-manager__backup {
    align-items: stretch;
    flex-direction: column;
  }
}

@media (max-height: 700px) {
  .install-manager {
    block-size: calc(100dvh - 16px);
  }

  .install-manager__header {
    gap: 10px;
    padding: 14px 54px 12px 14px;
  }

  .install-manager__header div {
    gap: 5px;
  }

  .install-manager__header h2 {
    font-size: 20px;
  }

  .install-manager__state {
    min-block-size: 28px;
    font-size: 11px;
    padding-inline: 10px;
  }

  .install-manager__summary div {
    gap: 5px;
    min-block-size: 76px;
    padding: 10px 12px;
  }

  .install-manager__summary dd {
    font-size: 13px;
  }

  .install-manager__backups {
    gap: 8px;
    padding: 12px 14px 14px;
  }

  .install-manager__backup {
    padding: 10px;
  }

  .install-manager__backup button {
    min-block-size: 32px;
    font-size: 12px;
    padding-inline: 12px;
  }
}
</style>
