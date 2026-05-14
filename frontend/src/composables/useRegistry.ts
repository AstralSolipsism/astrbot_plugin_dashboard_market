import { computed, onMounted, ref } from 'vue';
import { getPluginBridge } from '../lib/pluginBridge';
import type {
  DashboardRegistry,
  DashboardRegistryVersion,
  MarketStatus,
  PluginDashboardStatus,
  PluginMarketPayload
} from '../types/market';

const fallbackRegistry: DashboardRegistry = {
  schemaVersion: '2026-05-11',
  generatedAt: '2026-05-11T00:00:00.000Z',
  contracts: [
    {
      id: 'astrbot-dashboard-contract@v4.24.2',
      version: 'v4.24.2',
      astrbotVersion: '4.24.2',
      astrbotRef: '041c35c35bc9b2c2e6b853a880121751e22f348b',
      path: 'registry/contracts/v4.24.2.json'
    }
  ],
  dashboards: []
};

export function useRegistry() {
  const registry = ref<DashboardRegistry>(fallbackRegistry);
  const loading = ref(true);
  const error = ref('');
  const selectedId = ref('');
  const marketStatus = ref<MarketStatus>({});
  const status = ref<PluginDashboardStatus | undefined>();

  const dashboards = computed(() => registry.value.dashboards);
  const selectedDashboard = computed<DashboardRegistryVersion | undefined>(() =>
    dashboards.value.find((dashboard) => dashboard.id === selectedId.value) ?? dashboards.value[0]
  );
  const stats = computed(() => {
    const passed = dashboards.value.filter((dashboard) => dashboard.verification.status === 'passed').length;
    const contracts = new Set(dashboards.value.map((dashboard) => dashboard.compatibility.contract));
    return {
      total: dashboards.value.length,
      passed,
      contracts: contracts.size,
      mirrored: dashboards.value.filter((dashboard) => (dashboard.artifact.mirrors?.length ?? 0) > 0).length,
      mediaMirrored: marketStatus.value.mediaMirrors?.mirrored ?? 0,
      mediaFailed: marketStatus.value.mediaMirrors?.failed ?? 0
    };
  });

  async function loadRegistry(): Promise<void> {
    loading.value = true;
    error.value = '';
    try {
      const payload = await getPluginBridge().apiGet<PluginMarketPayload>('market');
      registry.value = {
        schemaVersion: 'plugin-market',
        generatedAt: new Date().toISOString(),
        contracts: [],
        dashboards: Array.isArray(payload.dashboards) ? payload.dashboards : []
      };
      marketStatus.value = { sync: payload.sync };
      if (payload.cached && payload.error) {
        error.value = payload.error;
      }
      selectedId.value = registry.value.dashboards[0]?.id ?? '';
      await loadStatus();
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause);
      registry.value = fallbackRegistry;
      selectedId.value = '';
      await loadStatus();
    } finally {
      loading.value = false;
    }
  }

  function selectDashboard(dashboard: DashboardRegistryVersion): void {
    selectedId.value = dashboard.id;
  }

  async function loadStatus(): Promise<void> {
    try {
      status.value = await getPluginBridge().apiGet<PluginDashboardStatus>('status');
    } catch {
      status.value = undefined;
    }
  }

  onMounted(() => {
    void loadRegistry();
  });

  return {
    dashboards,
    error,
    loadRegistry,
    loading,
    marketStatus,
    registry,
    selectDashboard,
    selectedDashboard,
    status,
    stats
  };
}
