<script setup lang="ts">
import { computed, shallowRef } from 'vue';
import BackupPanel from './components/BackupPanel.vue';
import DashboardDetailOverlay from './components/gallery/DashboardDetailOverlay.vue';
import GalleryCanvas from './components/gallery/GalleryCanvas.vue';
import GalleryNav from './components/gallery/GalleryNav.vue';
import MarketInfoPanel from './components/gallery/MarketInfoPanel.vue';
import { useRegistry } from './composables/useRegistry';
import { useI18n } from './composables/useI18n';
import { dashboardInstallKey, resolveDashboardInstallState } from './lib/installState';
import { getPluginBridge } from './lib/pluginBridge';
import type { GalleryItem } from './types/gallery';
import type {
  DashboardInstallDisplayState,
  DashboardRegistryVersion,
  PluginBackup,
  PluginInstallResult
} from './types/market';

const { dashboards, error, loadRegistry, loading, marketStatus, registry, stats, status } = useRegistry();
const { t } = useI18n();
const activeView = shallowRef<'gallery' | 'about'>('gallery');
const selectedItem = shallowRef<GalleryItem | undefined>();
const backupOpen = shallowRef(false);
const installingKey = shallowRef('');
const restoringBackupId = shallowRef('');
const operationError = shallowRef('');
const operationMessage = shallowRef('');

const installStates = computed<Record<string, DashboardInstallDisplayState>>(() => {
  return Object.fromEntries(
    dashboards.value.map((dashboard) => [
      dashboardInstallKey(dashboard),
      resolveDashboardInstallState(dashboard, status.value)
    ])
  );
});

const selectedInstallState = computed<DashboardInstallDisplayState>(() => {
  return selectedItem.value?.dashboard
    ? resolveDashboardInstallState(selectedItem.value.dashboard, status.value)
    : 'none';
});

function selectItem(item: GalleryItem): void {
  if (item.dashboard) {
    selectedItem.value = item;
  }
}

function closeDetail(): void {
  selectedItem.value = undefined;
}

function showGallery(): void {
  activeView.value = 'gallery';
}

function showAbout(): void {
  activeView.value = 'about';
  closeDetail();
}

function openBackupPanel(): void {
  activeView.value = 'gallery';
  backupOpen.value = true;
}

function closeBackupPanel(): void {
  backupOpen.value = false;
}

async function installDashboard(dashboard: DashboardRegistryVersion): Promise<void> {
  const key = `${dashboard.id}@${dashboard.version}`;
  if (installingKey.value || isInstalled(dashboard)) {
    return;
  }
  installingKey.value = key;
  operationError.value = '';
  operationMessage.value = '';
  try {
    const result = await getPluginBridge().apiPost<PluginInstallResult>('install', {
      id: dashboard.id,
      version: dashboard.version
    });
    if (result.status) {
      status.value = result.status;
    }
    operationMessage.value = result.activation?.message || t('install.success');
    await loadRegistry();
  } catch (cause) {
    operationError.value = cause instanceof Error ? cause.message : String(cause);
  } finally {
    installingKey.value = '';
  }
}

async function restoreBackup(backup: PluginBackup): Promise<void> {
  if (restoringBackupId.value) {
    return;
  }
  restoringBackupId.value = backup.id;
  operationError.value = '';
  operationMessage.value = '';
  try {
    const result = await getPluginBridge().apiPost<PluginInstallResult>('restore', {
      backupId: backup.id
    });
    if (result.status) {
      status.value = result.status;
    }
    operationMessage.value = t('install.restoreSuccess');
    await loadRegistry();
  } catch (cause) {
    operationError.value = cause instanceof Error ? cause.message : String(cause);
  } finally {
    restoringBackupId.value = '';
  }
}

function isInstalled(dashboard: DashboardRegistryVersion): boolean {
  return resolveDashboardInstallState(dashboard, status.value) !== 'none';
}
</script>

<template>
  <main class="app-shell">
    <GalleryNav
      :active-view="activeView"
      :last-updated-at="marketStatus.sync?.lastFinishedAt ?? registry.generatedAt"
      :passed="stats.passed"
      :total="stats.total"
      @show-about="showAbout"
      @show-gallery="showGallery"
    />
    <GalleryCanvas
      :dashboards="dashboards"
      :error="error"
      :install-states="installStates"
      :loading="loading"
      :stats="stats"
      @browse="showGallery"
      @retry="loadRegistry"
      @select="selectItem"
      @submit="openBackupPanel"
    />
    <MarketInfoPanel
      :last-updated-at="marketStatus.sync?.lastFinishedAt ?? registry.generatedAt"
      :open="activeView === 'about'"
      :passed="stats.passed"
      :total="stats.total"
      @close="showGallery"
      @submit="openBackupPanel"
    />
    <DashboardDetailOverlay
      :install-state="selectedInstallState"
      :installing-key="installingKey"
      :item="selectedItem"
      @close="closeDetail"
      @install="installDashboard"
    />
    <BackupPanel
      :open="backupOpen"
      :restoring-backup-id="restoringBackupId"
      :status="status"
      @close="closeBackupPanel"
      @restore="restoreBackup"
    />
    <section v-if="operationError || operationMessage" class="app-shell__toast" role="status" data-no-pan="true">
      <span :data-state="operationError ? 'failed' : 'ok'">{{ operationError || operationMessage }}</span>
      <button type="button" :aria-label="t('detail.close')" @click="operationError = ''; operationMessage = ''">
        {{ t('detail.close') }}
      </button>
    </section>
  </main>
</template>

<style scoped>
.app-shell__toast {
  position: fixed;
  z-index: 90;
  inset-inline: 24px;
  inset-block-end: 24px;
  display: flex;
  max-inline-size: min(680px, calc(100vw - 48px));
  align-items: center;
  gap: 10px;
  justify-content: space-between;
  border: 1px solid oklch(0.78 0.035 145 / 78%);
  border-radius: 999px;
  background: oklch(0.96 0.032 145 / 90%);
  box-shadow: 0 18px 46px oklch(0.18 0.006 110 / 12%);
  color: oklch(0.26 0.05 145);
  padding: 6px 6px 6px 16px;
  backdrop-filter: blur(14px);
}

.app-shell__toast span {
  min-inline-size: 0;
  overflow-wrap: anywhere;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
}

.app-shell__toast span[data-state="failed"] {
  color: oklch(0.42 0.1 28);
}

.app-shell__toast button {
  flex: 0 0 auto;
  min-block-size: 34px;
  border: 0;
  border-radius: 999px;
  background: oklch(0.18 0.004 110);
  color: oklch(0.97 0.006 110);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  padding-inline: 14px;
}

@media (max-width: 720px) {
  .app-shell__toast {
    inset-inline: 12px;
    inset-block-end: 12px;
    max-inline-size: none;
    border-radius: 14px;
  }
}
</style>
