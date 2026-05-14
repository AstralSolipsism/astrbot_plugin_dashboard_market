import { computed, readonly, shallowRef } from 'vue';
import { messages, type Locale, type MessageKey } from '../i18n/messages';

type MessageParams = Record<string, string | number>;

const storageKey = 'astrbot-dashboard-market-locale';
const supportedLocales = Object.keys(messages) as Locale[];
const locale = shallowRef<Locale>(resolveInitialLocale());

applyDocumentLocale(locale.value);

export function useI18n() {
  const languageTargetLabel = computed(() => messages[locale.value]['nav.languageTarget']);

  function t(key: MessageKey | string, params: MessageParams = {}): string {
    const template = resolveMessage(key);
    return interpolate(template, params);
  }

  function setLocale(nextLocale: Locale): void {
    locale.value = nextLocale;
    persistLocale(nextLocale);
    applyDocumentLocale(nextLocale);
  }

  function toggleLocale(): void {
    setLocale(locale.value === 'en' ? 'zh-CN' : 'en');
  }

  function statusLabel(status: string): string {
    return t(`status.${status}`);
  }

  return {
    languageTargetLabel,
    locale: readonly(locale),
    setLocale,
    statusLabel,
    t,
    toggleLocale
  };
}

function resolveInitialLocale(): Locale {
  const bridgeLocale = normalizeLocale(window.AstrBotPluginPage?.getLocale?.());
  if (bridgeLocale) {
    return bridgeLocale;
  }

  const storedLocale = readStoredLocale();
  if (storedLocale) {
    return storedLocale;
  }

  if (typeof navigator !== 'undefined' && navigator.language.toLowerCase().startsWith('zh')) {
    return 'zh-CN';
  }

  return 'en';
}

window.AstrBotPluginPage?.onContext?.((context) => {
  const nextLocale = normalizeLocale(context?.locale);
  if (nextLocale && nextLocale !== locale.value) {
    locale.value = nextLocale;
    applyDocumentLocale(nextLocale);
  }
});

function readStoredLocale(): Locale | undefined {
  if (typeof localStorage === 'undefined') {
    return undefined;
  }

  try {
    const value = localStorage.getItem(storageKey);
    return isSupportedLocale(value) ? value : undefined;
  } catch {
    return undefined;
  }
}

function persistLocale(nextLocale: Locale): void {
  if (typeof localStorage === 'undefined') {
    return;
  }

  try {
    localStorage.setItem(storageKey, nextLocale);
  } catch {
    // Local storage can be unavailable in privacy modes.
  }
}

function applyDocumentLocale(nextLocale: Locale): void {
  if (typeof document === 'undefined') {
    return;
  }

  document.documentElement.lang = nextLocale;
  document.title = messages[nextLocale]['meta.title'];
}

function resolveMessage(key: MessageKey | string): string {
  const currentMessages = messages[locale.value] as Record<string, string>;
  const fallbackMessages = messages.en as Record<string, string>;
  return currentMessages[key] ?? fallbackMessages[key] ?? key;
}

function interpolate(template: string, params: MessageParams): string {
  return template.replace(/\{(\w+)\}/g, (_, name: string) => String(params[name] ?? `{${name}}`));
}

function isSupportedLocale(value: string | null): value is Locale {
  return supportedLocales.includes(value as Locale);
}

function normalizeLocale(value: string | undefined): Locale | undefined {
  if (!value) {
    return undefined;
  }
  const normalized = value.toLowerCase();
  if (normalized.startsWith('zh')) {
    return 'zh-CN';
  }
  if (normalized.startsWith('en')) {
    return 'en';
  }
  return isSupportedLocale(value) ? value : undefined;
}
