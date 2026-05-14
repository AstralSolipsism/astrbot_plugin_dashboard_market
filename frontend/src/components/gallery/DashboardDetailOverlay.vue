<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../../composables/useI18n';
import { dashboardInstallKey } from '../../lib/installState';
import { hasMediaMirrorFailure, mediaAssetUrl, mediaMirrorLabel } from '../../lib/media';
import type { GalleryItem } from '../../types/gallery';
import type {
  DashboardInstallDisplayState,
  DashboardRegistryVersion,
  MediaAsset
} from '../../types/market';
import ModalShell from '../ModalShell.vue';

const props = withDefaults(
  defineProps<{
    installState?: DashboardInstallDisplayState;
    installingKey: string;
    item: GalleryItem | undefined;
  }>(),
  {
    installState: 'none'
  }
);

const emit = defineEmits<{
  close: [];
  install: [dashboard: DashboardRegistryVersion];
}>();

const { statusLabel, t } = useI18n();

const dashboard = computed(() => props.item?.dashboard);
const cover = computed(() => dashboard.value?.media.effectiveCover);
const screenshots = computed(() => dashboard.value?.media.effectiveScreenshots ?? []);
const coverUrl = computed(() => mediaAssetUrl(cover.value) || props.item?.imageUrl || '');
const coverage = computed(() => dashboard.value?.verification.coverage);
const authors = computed(() => dashboard.value?.project.authors.map((author) => author.name).join(', ') ?? '');
const reportUrl = computed(() => coverage.value?.reportUrl ?? dashboard.value?.verification.report);
const installKey = computed(() => (dashboard.value ? dashboardInstallKey(dashboard.value) : ''));
const installing = computed(() => Boolean(installKey.value) && props.installingKey === installKey.value);
const installBlocked = computed(() => Boolean(props.installingKey) || props.installState !== 'none');
const installLabel = computed(() => {
  if (installing.value) {
    return t('detail.installing');
  }

  switch (props.installState) {
    case 'current':
      return t('detail.current');
    case 'installed':
      return t('detail.installed');
    case 'restartRequired':
      return t('detail.restartRequired');
    default:
      return props.installingKey ? t('detail.installing') : t('detail.install');
  }
});
const installStateLabel = computed(() => labelForInstallState(props.installState));
const mirrorStatus = computed(() =>
  (dashboard.value?.artifact.mirrors?.length ?? 0) > 0 ? t('detail.mirrored') : t('detail.originalArtifact')
);
const mediaStatus = computed(() => {
  const assets = [cover.value, ...screenshots.value].filter((asset): asset is MediaAsset => Boolean(asset));
  if (hasMediaMirrorFailure(assets)) {
    return t('detail.mediaMirrorFailed');
  }
  return t(`detail.${mediaMirrorLabel(cover.value ?? screenshots.value[0])}`);
});

function close(): void {
  emit('close');
}

function install(): void {
  if (dashboard.value && !installBlocked.value) {
    emit('install', dashboard.value);
  }
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
    :aria-label="dashboard ? t('detail.dialogLabel', { name: dashboard.project.name }) : t('detail.close')"
    :close-label="t('detail.close')"
    :open="Boolean(dashboard)"
    size="wide"
    @close="close"
  >
    <article v-if="dashboard" class="dashboard-detail">
      <header class="dashboard-detail__header">
        <div class="dashboard-detail__cover">
          <img v-if="cover" :alt="cover.alt" :src="coverUrl" />
          <img v-else :alt="props.item?.title" :src="coverUrl" />
        </div>

        <div class="dashboard-detail__intro">
          <div class="dashboard-detail__badges">
            <span class="dashboard-detail__state" :data-state="installState">
              {{ installStateLabel }}
            </span>
            <span class="dashboard-detail__status" :data-status="dashboard.verification.status">
              {{ statusLabel(dashboard.verification.status) }}
            </span>
            <span class="dashboard-detail__version">{{ t('detail.version') }} {{ dashboard.version }}</span>
          </div>

          <div class="dashboard-detail__title">
            <h2>{{ dashboard.project.name }}</h2>
            <p>{{ dashboard.project.description }}</p>
          </div>

          <div class="dashboard-detail__actions">
            <button
              type="button"
              :data-state="installState"
              :disabled="installBlocked"
              data-autofocus
              @click="install"
            >
              {{ installLabel }}
            </button>
            <a :href="dashboard.source.repo" rel="noreferrer" target="_blank">{{ t('detail.source') }}</a>
            <a :href="dashboard.project.homepage" rel="noreferrer" target="_blank">{{ t('detail.homepage') }}</a>
            <a v-if="reportUrl" :href="reportUrl" rel="noreferrer" target="_blank">{{ t('detail.report') }}</a>
          </div>
        </div>
      </header>

      <div class="dashboard-detail__content">
        <section class="dashboard-detail__section" :aria-label="t('detail.compatibility')">
          <h3>{{ t('detail.compatibility') }}</h3>
          <dl class="dashboard-detail__facts">
            <div>
              <dt>{{ t('detail.astrbot') }}</dt>
              <dd>{{ dashboard.compatibility.astrbot }}</dd>
            </div>
            <div>
              <dt>{{ t('detail.contract') }}</dt>
              <dd>{{ dashboard.compatibility.contract }}</dd>
            </div>
            <div>
              <dt>{{ t('detail.authors') }}</dt>
              <dd>{{ authors }}</dd>
            </div>
          </dl>
        </section>

        <section class="dashboard-detail__section" :aria-label="t('detail.package')">
          <h3>{{ t('detail.package') }}</h3>
          <dl class="dashboard-detail__facts">
            <div>
              <dt>{{ t('detail.sha256') }}</dt>
              <dd class="dashboard-detail__hash">{{ dashboard.artifact.sha256 }}</dd>
            </div>
            <div>
              <dt>{{ t('detail.mirror') }}</dt>
              <dd>{{ mirrorStatus }}</dd>
            </div>
            <div>
              <dt>{{ t('detail.mediaMirror') }}</dt>
              <dd>{{ mediaStatus }}</dd>
            </div>
          </dl>
        </section>

        <section v-if="coverage" class="dashboard-detail__section" :aria-label="t('detail.coverageLabel')">
          <h3>{{ t('detail.coverage') }}</h3>
          <div class="dashboard-detail__coverage">
            <span>
              {{
                t('detail.capabilities', {
                  covered: coverage.coveredCapabilities,
                  required: coverage.requiredCapabilities
                })
              }}
            </span>
            <span>{{ t('detail.apis', { covered: coverage.coveredApis, required: coverage.requiredApis }) }}</span>
            <span>{{ statusLabel(coverage.status) }}</span>
          </div>
        </section>

        <section v-if="screenshots.length > 0" class="dashboard-detail__section" :aria-label="t('detail.previewsLabel')">
          <h3>{{ t('detail.previews') }}</h3>
          <div class="dashboard-detail__preview-list">
            <figure v-for="asset in screenshots" :key="asset.url">
              <img :alt="asset.alt" :src="mediaAssetUrl(asset)" />
              <figcaption>
                {{ asset.label ?? asset.route ?? asset.viewport ?? asset.source }}
                <span v-if="asset.mirrorStatus === 'failed'">{{ t('detail.mediaMirrorFailed') }}</span>
              </figcaption>
            </figure>
          </div>
        </section>
      </div>
    </article>
  </ModalShell>
</template>

<style scoped>
.dashboard-detail {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  block-size: min(780px, calc(100dvh - 36px));
  min-block-size: 0;
}

.dashboard-detail__header {
  display: grid;
  grid-template-columns: minmax(260px, 0.75fr) minmax(0, 1fr);
  gap: 18px;
  padding: 18px 62px 16px 18px;
  border-block-end: 1px solid oklch(0.86 0.006 110);
  background: oklch(0.98 0.006 110);
}

.dashboard-detail__cover {
  overflow: hidden;
  align-self: start;
  aspect-ratio: 16 / 10;
  border: 1px solid oklch(0.84 0.006 110);
  border-radius: 8px;
  background: oklch(0.92 0.006 110);
}

.dashboard-detail__cover img {
  display: block;
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
}

.dashboard-detail__intro {
  display: grid;
  min-inline-size: 0;
  align-content: start;
  gap: 14px;
}

.dashboard-detail__badges,
.dashboard-detail__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dashboard-detail__state,
.dashboard-detail__status,
.dashboard-detail__version {
  display: inline-flex;
  max-inline-size: 100%;
  min-block-size: 28px;
  align-items: center;
  border-radius: 999px;
  overflow: hidden;
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0;
  line-height: 1;
  padding-inline: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-detail__state {
  background: oklch(0.91 0.006 110);
  color: oklch(0.36 0.006 110);
}

.dashboard-detail__state[data-state="current"] {
  background: oklch(0.9 0.055 150);
  color: oklch(0.27 0.08 150);
}

.dashboard-detail__state[data-state="restartRequired"] {
  background: oklch(0.94 0.052 78);
  color: oklch(0.34 0.07 70);
}

.dashboard-detail__status,
.dashboard-detail__version {
  background: oklch(0.93 0.006 110);
  color: oklch(0.36 0.006 110);
}

.dashboard-detail__status[data-status="passed"] {
  background: oklch(0.91 0.045 150);
  color: oklch(0.32 0.08 150);
}

.dashboard-detail__status[data-status="failed"] {
  background: oklch(0.92 0.055 28);
  color: oklch(0.38 0.095 28);
}

.dashboard-detail__title {
  display: grid;
  gap: 8px;
  min-inline-size: 0;
}

.dashboard-detail__title h2 {
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.16 0.004 110);
  font-size: 30px;
  font-weight: 780;
  letter-spacing: 0;
  line-height: 1.08;
}

.dashboard-detail__title p {
  margin: 0;
  max-inline-size: 62ch;
  overflow-wrap: anywhere;
  color: oklch(0.39 0.006 110);
  font-size: 14px;
  line-height: 1.5;
}

.dashboard-detail__actions {
  align-items: center;
}

.dashboard-detail__actions a,
.dashboard-detail__actions button {
  display: inline-flex;
  min-block-size: 38px;
  align-items: center;
  justify-content: center;
  border: 1px solid oklch(0.2 0.004 110);
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

.dashboard-detail__actions a {
  background: oklch(0.985 0.006 110);
  color: oklch(0.17 0.004 110);
}

.dashboard-detail__actions a:hover,
.dashboard-detail__actions a:focus-visible,
.dashboard-detail__actions button:hover,
.dashboard-detail__actions button:focus-visible {
  background: oklch(0.27 0.006 110);
  color: oklch(0.98 0.006 110);
}

.dashboard-detail__actions button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.dashboard-detail__content {
  display: grid;
  min-block-size: 0;
  gap: 14px;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 16px 18px 18px;
}

.dashboard-detail__section {
  display: grid;
  gap: 10px;
}

.dashboard-detail__section h3 {
  margin: 0;
  color: oklch(0.22 0.004 110);
  font-size: 14px;
  font-weight: 780;
  letter-spacing: 0;
}

.dashboard-detail__facts {
  display: grid;
  gap: 1px;
  overflow: hidden;
  margin: 0;
  border: 1px solid oklch(0.84 0.006 110);
  border-radius: 8px;
  background: oklch(0.84 0.006 110);
}

.dashboard-detail__facts div {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
  background: oklch(0.985 0.006 110);
  padding: 12px 14px;
}

.dashboard-detail__facts dt {
  color: oklch(0.46 0.006 110);
  font-size: 12px;
  font-weight: 720;
}

.dashboard-detail__facts dd {
  min-inline-size: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.2 0.004 110);
  font-size: 13px;
  font-weight: 620;
  line-height: 1.38;
}

.dashboard-detail__hash {
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
}

.dashboard-detail__coverage {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.dashboard-detail__coverage span {
  display: grid;
  min-block-size: 66px;
  place-items: center;
  border: 1px solid oklch(0.84 0.006 110);
  border-radius: 8px;
  background: oklch(0.965 0.006 110);
  color: oklch(0.25 0.005 110);
  font-size: 12px;
  font-weight: 720;
  line-height: 1.3;
  padding: 10px;
  text-align: center;
}

.dashboard-detail__preview-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}

.dashboard-detail__preview-list figure {
  overflow: hidden;
  margin: 0;
  border: 1px solid oklch(0.84 0.006 110);
  border-radius: 8px;
  background: oklch(0.955 0.006 110);
}

.dashboard-detail__preview-list img {
  display: block;
  inline-size: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

.dashboard-detail__preview-list figcaption {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 9px 11px;
  overflow-wrap: anywhere;
  color: oklch(0.45 0.005 110);
  font-size: 12px;
  font-weight: 640;
  letter-spacing: 0;
}

@media (max-width: 760px) {
  .dashboard-detail {
    block-size: calc(100dvh - 16px);
  }

  .dashboard-detail__header {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 54px 12px 14px;
  }

  .dashboard-detail__title h2 {
    font-size: 25px;
  }

  .dashboard-detail__content {
    padding: 14px 12px 16px;
  }

  .dashboard-detail__facts div,
  .dashboard-detail__coverage {
    grid-template-columns: 1fr;
  }

  .dashboard-detail__actions a,
  .dashboard-detail__actions button {
    flex: 1 1 136px;
  }
}
</style>
