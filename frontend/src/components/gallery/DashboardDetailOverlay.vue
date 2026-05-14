<script setup lang="ts">
import { openExternalUrl as openExternal } from '../../lib/openExternal';
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
import DashboardPreviewCarousel from './DashboardPreviewCarousel.vue';
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
const previewAssets = computed(() => screenshots.value);
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
    tone="market"
    @close="close"
  >
    <article v-if="dashboard" class="dashboard-detail">
      <header class="dashboard-detail__header">
        <div class="dashboard-detail__cover">
          <img v-if="coverUrl" :alt="cover?.alt ?? props.item?.title" :src="coverUrl" />
          <div v-else class="dashboard-detail__cover-empty">
            {{ t('detail.previewEmpty') }}
          </div>
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
            <a :href="dashboard.source.repo" rel="noreferrer" target="_blank" @click.prevent.stop="openExternal(dashboard.source.repo)">{{ t('detail.source') }}</a>
            <a :href="dashboard.project.homepage" rel="noreferrer" target="_blank" @click.prevent.stop="openExternal(dashboard.project.homepage)">{{ t('detail.homepage') }}</a>
            <a v-if="reportUrl" :href="reportUrl" rel="noreferrer" target="_blank" @click.prevent.stop="openExternal(reportUrl)">{{ t('detail.report') }}</a>
          </div>
        </div>
      </header>

      <div class="dashboard-detail__content">
        <div class="dashboard-detail__info-grid">
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
        </div>

        <section class="dashboard-detail__section dashboard-detail__section--previews" :aria-label="t('detail.previewsLabel')">
          <div class="dashboard-detail__section-heading">
            <h3>{{ t('detail.previews') }}</h3>
          </div>
          <DashboardPreviewCarousel :assets="previewAssets" />
        </section>
      </div>
    </article>
  </ModalShell>
</template>

<style scoped>
.dashboard-detail {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  block-size: min(820px, calc(100dvh - 36px));
  min-block-size: 0;
  background:
    radial-gradient(circle at 12% 0%, oklch(0.62 0.13 205 / 12%), transparent 32%),
    radial-gradient(circle at 88% 10%, oklch(0.62 0.08 86 / 10%), transparent 28%);
  color: oklch(0.92 0.018 215);
}

.dashboard-detail__header {
  display: grid;
  grid-template-columns: minmax(190px, 248px) minmax(0, 1fr);
  gap: 10px;
  padding: 14px 58px 12px 14px;
  border-block-end: 1px solid oklch(0.7 0.1 205 / 18%);
  background:
    linear-gradient(180deg, oklch(0.12 0.028 242 / 72%), oklch(0.07 0.019 248 / 52%)),
    radial-gradient(circle at 24% 0%, oklch(0.68 0.14 205 / 12%), transparent 34%);
}

.dashboard-detail__cover {
  overflow: hidden;
  align-self: start;
  aspect-ratio: 16 / 9;
  border: 1px solid oklch(0.7 0.11 205 / 24%);
  border-radius: 10px;
  background:
    radial-gradient(circle at 28% 22%, oklch(0.66 0.13 205 / 18%), transparent 32%),
    oklch(0.045 0.016 250);
  box-shadow:
    0 18px 44px oklch(0.02 0.018 255 / 34%),
    inset 0 1px 0 oklch(0.86 0.08 205 / 10%);
}

.dashboard-detail__cover img {
  display: block;
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
}

.dashboard-detail__cover-empty {
  display: grid;
  block-size: 100%;
  min-block-size: 136px;
  place-items: center;
  color: oklch(0.78 0.06 210);
  font-size: 12px;
  font-weight: 720;
}

.dashboard-detail__intro {
  display: grid;
  min-inline-size: 0;
  align-content: start;
  gap: 10px;
}

.dashboard-detail__badges,
.dashboard-detail__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dashboard-detail__state,
.dashboard-detail__status,
.dashboard-detail__version {
  display: inline-flex;
  max-inline-size: 100%;
  min-block-size: 26px;
  align-items: center;
  border-radius: 999px;
  overflow: hidden;
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0;
  line-height: 1;
  padding-inline: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-detail__state {
  border: 1px solid oklch(0.72 0.1 205 / 18%);
  background: oklch(0.12 0.022 245 / 78%);
  color: oklch(0.82 0.046 210);
}

.dashboard-detail__state[data-state="current"] {
  background: oklch(0.74 0.13 205 / 20%);
  color: oklch(0.9 0.07 205);
}

.dashboard-detail__state[data-state="restartRequired"] {
  background: oklch(0.76 0.1 78 / 22%);
  color: oklch(0.88 0.09 84);
}

.dashboard-detail__status,
.dashboard-detail__version {
  border: 1px solid oklch(0.72 0.1 205 / 16%);
  background: oklch(0.1 0.02 245 / 72%);
  color: oklch(0.78 0.042 214);
}

.dashboard-detail__status[data-status="passed"] {
  background: oklch(0.7 0.13 205 / 18%);
  color: oklch(0.9 0.07 205);
}

.dashboard-detail__status[data-status="failed"] {
  background: oklch(0.62 0.13 28 / 20%);
  color: oklch(0.82 0.11 32);
}

.dashboard-detail__title {
  display: grid;
  gap: 6px;
  min-inline-size: 0;
}

.dashboard-detail__title h2 {
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.96 0.018 215);
  font-size: 26px;
  font-weight: 780;
  letter-spacing: 0;
  line-height: 1.08;
}

.dashboard-detail__title p {
  margin: 0;
  max-inline-size: 62ch;
  overflow-wrap: anywhere;
  color: oklch(0.74 0.038 214);
  font-size: 12px;
  line-height: 1.42;
}

.dashboard-detail__actions {
  align-items: center;
}

.dashboard-detail__actions a,
.dashboard-detail__actions button {
  display: inline-flex;
  min-block-size: 34px;
  align-items: center;
  justify-content: center;
  border: 1px solid oklch(0.76 0.12 205 / 28%);
  border-radius: 999px;
  background: oklch(0.7 0.13 205);
  color: oklch(0.04 0.016 245);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0;
  padding-inline: 13px;
  text-decoration: none;
}

.dashboard-detail__actions a {
  background: oklch(0.08 0.02 245 / 72%);
  color: oklch(0.88 0.06 205);
}

.dashboard-detail__actions a:hover,
.dashboard-detail__actions a:focus-visible,
.dashboard-detail__actions button:hover,
.dashboard-detail__actions button:focus-visible {
  background: oklch(0.9 0.08 205);
  color: oklch(0.035 0.016 245);
}

.dashboard-detail__actions button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.dashboard-detail__content {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-block-size: 0;
  gap: 12px;
  overflow: hidden;
  overscroll-behavior: contain;
  padding: 12px 14px 14px;
  scrollbar-color: oklch(0.7 0.13 205 / 44%) transparent;
}

.dashboard-detail__info-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  min-inline-size: 0;
}

.dashboard-detail__section {
  display: grid;
  gap: 10px;
  min-inline-size: 0;
  border: 1px solid oklch(0.7 0.1 205 / 16%);
  border-radius: 12px;
  background: oklch(0.065 0.017 248 / 58%);
  box-shadow: inset 0 1px 0 oklch(0.86 0.08 205 / 6%);
  padding: 8px;
}

.dashboard-detail__section--previews {
  grid-template-rows: auto minmax(0, 1fr);
  min-block-size: 0;
  background: transparent;
  border-color: transparent;
  box-shadow: none;
  padding: 0;
}

.dashboard-detail__section-heading {
  padding-inline: 2px;
}

.dashboard-detail__section h3 {
  margin: 0;
  color: oklch(0.9 0.06 205);
  font-size: 12px;
  font-weight: 780;
  letter-spacing: 0.01em;
}

.dashboard-detail__facts {
  display: grid;
  gap: 1px;
  overflow: hidden;
  margin: 0;
  border: 1px solid oklch(0.7 0.1 205 / 16%);
  border-radius: 10px;
  background: oklch(0.7 0.1 205 / 12%);
}

.dashboard-detail__facts div {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  background: oklch(0.055 0.016 248 / 86%);
  padding: 12px 14px;
}

.dashboard-detail__facts dt {
  color: oklch(0.66 0.05 210);
  font-size: 12px;
  font-weight: 720;
}

.dashboard-detail__facts dd {
  min-inline-size: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: oklch(0.88 0.025 215);
  font-size: 12px;
  font-weight: 620;
  line-height: 1.38;
}

.dashboard-detail__hash {
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
}

.dashboard-detail__coverage {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.dashboard-detail__coverage span {
  display: grid;
  min-block-size: 42px;
  place-items: center;
  border: 1px solid oklch(0.7 0.1 205 / 18%);
  border-radius: 10px;
  background:
    radial-gradient(circle at 28% 20%, oklch(0.7 0.13 205 / 12%), transparent 42%),
    oklch(0.055 0.016 248 / 82%);
  color: oklch(0.86 0.04 214);
  font-size: 12px;
  font-weight: 720;
  line-height: 1.3;
  padding: 8px;
  text-align: center;
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
