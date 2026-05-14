/// <reference types="vite/client" />

import type { AstrBotPluginPageBridge } from './lib/pluginBridge';

declare global {
  interface Window {
    AstrBotPluginPage?: AstrBotPluginPageBridge;
  }
}

export {};
