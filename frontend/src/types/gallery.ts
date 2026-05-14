import type { DashboardInstallDisplayState, DashboardRegistryVersion } from './market';

export interface GalleryItem {
  id: string;
  title: string;
  description: string;
  imageUrl: string;
  authorId: string;
  repositoryUrl: string;
  x: number;
  y: number;
  status: string;
  previewFailed?: boolean;
  installState?: DashboardInstallDisplayState;
  dashboard?: DashboardRegistryVersion;
}
