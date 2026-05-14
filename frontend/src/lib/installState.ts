import type {
  DashboardInstallDisplayState,
  DashboardRegistryVersion,
  PluginDashboardStatus
} from '../types/market';

export function dashboardInstallKey(dashboard: Pick<DashboardRegistryVersion, 'id' | 'version'>): string {
  return `${dashboard.id}@${dashboard.version}`;
}

export function resolveDashboardInstallState(
  dashboard: Pick<DashboardRegistryVersion, 'id' | 'version'>,
  status: PluginDashboardStatus | undefined
): DashboardInstallDisplayState {
  const installed = status?.installed?.dashboard;
  if (!installed || installed.id !== dashboard.id || installed.version !== dashboard.version) {
    return 'none';
  }

  return resolveRuntimeInstallState(status);
}

export function resolveRuntimeInstallState(
  status: PluginDashboardStatus | undefined
): DashboardInstallDisplayState {
  if (!status?.installed?.dashboard) {
    return 'none';
  }

  if (status.runtime.requiresRestart) {
    return 'restartRequired';
  }

  if (status.runtime.usesDataDist) {
    return 'current';
  }

  return 'installed';
}
