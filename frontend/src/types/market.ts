export type VerificationStatus = 'pending' | 'passed' | 'failed' | 'draft';
export type MediaAssetSource = 'author' | 'ci' | 'maintainer';
export type MediaViewport = 'desktop' | 'mobile' | 'tablet';
export type SyncStatus = 'idle' | 'running' | 'passed' | 'failed';
export type MirrorStatus = 'missing' | 'mirrored' | 'failed';
export type DashboardInstallDisplayState = 'none' | 'installed' | 'current' | 'restartRequired';

export interface DashboardAuthor {
  name: string;
  url?: string;
}

export interface MediaAsset {
  url: string;
  alt: string;
  label?: string;
  route?: string;
  viewport?: MediaViewport;
  source: MediaAssetSource;
  width?: number;
  height?: number;
  sha256: string;
  mirrors?: MediaAssetMirror[];
  preferredUrl?: string;
  mirrorStatus?: MirrorStatus;
}

export interface MediaAssetMirror {
  url: string;
  sha256: string;
  source: 'market';
  mirroredAt: string;
}

export interface DashboardMedia {
  cover?: MediaAsset;
  screenshots: MediaAsset[];
  demoUrl?: string;
  videoUrl?: string;
}

export interface DashboardRegistryMedia extends DashboardMedia {
  effectiveCover?: MediaAsset;
  effectiveScreenshots: MediaAsset[];
  ciScreenshots?: MediaAsset[];
}

export interface DashboardProjectManifest {
  id: string;
  name: string;
  description: string;
  authors: DashboardAuthor[];
  sourceRepo: string;
  license: string;
  homepage: string;
  tags: string[];
  media: DashboardMedia;
}

export interface DashboardSourceReference {
  repo: string;
  ref: string;
  commit?: string;
  directory?: string;
  packageManager?: 'pnpm' | 'npm' | 'yarn' | 'bun';
  build?: string;
  dist?: string;
}

export interface DashboardArtifactReference {
  url: string;
  sha256: string;
  size?: number;
  mirrors?: DashboardArtifactMirror[];
  preferredUrl?: string;
}

export interface DashboardArtifactMirror {
  url: string;
  sha256: string;
  source: 'market';
  mirroredAt: string;
}

export interface DashboardCompatibility {
  astrbot: string;
  contract: string;
}

export interface DashboardCoverageSummary {
  contract: string;
  status: VerificationStatus;
  requiredCapabilities: number;
  coveredCapabilities: number;
  requiredApis: number;
  coveredApis: number;
  reportUrl?: string;
  previewBaseUrl?: string;
  generatedAt?: string;
}

export interface DashboardGeneratedMedia {
  cover?: MediaAsset;
  screenshots?: MediaAsset[];
}

export interface DashboardVerification {
  status: VerificationStatus;
  workflowRun?: string;
  verifiedAt?: string;
  report?: string;
  coverage?: DashboardCoverageSummary;
  generatedMedia?: DashboardGeneratedMedia;
}

export interface DashboardVersionManifest {
  id: string;
  version: string;
  source: DashboardSourceReference;
  artifact: DashboardArtifactReference;
  compatibility: DashboardCompatibility;
  verification: DashboardVerification;
}

export interface DashboardRegistryVersion extends DashboardVersionManifest {
  project: DashboardProjectManifest;
  media: DashboardRegistryMedia;
}

export interface ContractSummary {
  id: string;
  version: string;
  astrbotVersion: string;
  astrbotRef: string;
  path: string;
}

export interface DashboardRegistry {
  schemaVersion: string;
  generatedAt: string;
  contracts: ContractSummary[];
  dashboards: DashboardRegistryVersion[];
}

export interface MarketStatus {
  sync?: {
    status: SyncStatus;
    lastCommit?: string;
    lastStartedAt?: string;
    lastFinishedAt?: string;
    lastError?: string;
  };
  mediaMirrors?: {
    missing: number;
    mirrored: number;
    failed: number;
  };
}

export interface PluginBackup {
  id: string;
  createdAt: string;
  sourceVersion?: string | null;
  path?: string;
  size?: number;
}

export interface PluginInstallState {
  dashboard?: {
    id: string;
    version: string;
  };
  artifact?: {
    url: string;
    sha256: string;
  };
  installedAt?: string;
  restoredBackup?: {
    id: string;
    sourceVersion?: string | null;
  };
  restoredAt?: string;
  astrbotVersion?: string;
  backup?: PluginBackup | null;
}

export interface PluginDashboardStatus {
  astrbotVersion: string;
  dist: {
    path: string;
    exists: boolean;
    version?: string | null;
  };
  runtime: {
    dashboardPath?: string | null;
    usesDataDist: boolean;
    requiresRestart: boolean;
  };
  installed?: PluginInstallState | null;
  backups: PluginBackup[];
}

export interface PluginMarketPayload {
  dashboards: DashboardRegistryVersion[];
  sync?: MarketStatus['sync'];
  cached?: boolean;
  error?: string | null;
  marketBaseUrl?: string;
}

export interface PluginInstallResult {
  dashboard?: {
    id: string;
    version: string;
  };
  backup?: PluginBackup | null;
  restoredBackup?: {
    id: string;
    sourceVersion?: string | null;
  };
  activation?: {
    message?: string;
  };
  status?: PluginDashboardStatus;
}
