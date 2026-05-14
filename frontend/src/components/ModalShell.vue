<script setup lang="ts">
import { nextTick, onBeforeUnmount, shallowRef, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    ariaLabel?: string;
    closeLabel?: string;
    labelledBy?: string;
    open: boolean;
    size?: 'narrow' | 'medium' | 'wide';
    tone?: 'default' | 'market';
  }>(),
  {
    size: 'medium',
    tone: 'default'
  }
);

const emit = defineEmits<{
  close: [];
}>();

const panel = shallowRef<HTMLElement>();
let previousFocus: Element | null = null;
let previousBodyOverflow = '';

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(',');

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      unlockBodyScroll();
      restoreFocus();
      return;
    }

    previousFocus = document.activeElement;
    lockBodyScroll();
    await nextTick();
    focusInitialElement();
  },
  { flush: 'post' }
);

onBeforeUnmount(() => {
  unlockBodyScroll();
});

function close(): void {
  emit('close');
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.stopPropagation();
    close();
    return;
  }

  if (event.key === 'Tab') {
    trapFocus(event);
  }
}

function focusInitialElement(): void {
  const currentPanel = panel.value;
  if (!currentPanel) {
    return;
  }

  const target =
    currentPanel.querySelector<HTMLElement>('[data-autofocus]:not([disabled])') ??
    getFocusableElements()[0] ??
    currentPanel;
  target.focus({ preventScroll: true });
}

function trapFocus(event: KeyboardEvent): void {
  const focusable = getFocusableElements();
  if (focusable.length === 0) {
    event.preventDefault();
    panel.value?.focus({ preventScroll: true });
    return;
  }

  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const active = document.activeElement;

  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus({ preventScroll: true });
    return;
  }

  if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus({ preventScroll: true });
  }
}

function getFocusableElements(): HTMLElement[] {
  return Array.from(panel.value?.querySelectorAll<HTMLElement>(focusableSelector) ?? []).filter((element) => {
    return (
      !element.hasAttribute('disabled') &&
      Boolean(element.offsetWidth || element.offsetHeight || element.getClientRects().length)
    );
  });
}

function lockBodyScroll(): void {
  previousBodyOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
}

function unlockBodyScroll(): void {
  if (document.body.style.overflow === 'hidden') {
    document.body.style.overflow = previousBodyOverflow;
  }
}

function restoreFocus(): void {
  if (previousFocus instanceof HTMLElement) {
    previousFocus.focus({ preventScroll: true });
  }
  previousFocus = null;
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal-shell" :data-tone="tone" data-no-pan="true" @click.self="close">
      <section
        ref="panel"
        class="modal-shell__panel"
        :aria-label="ariaLabel"
        :aria-labelledby="labelledBy"
        aria-modal="true"
        :data-size="size"
        :data-tone="tone"
        role="dialog"
        tabindex="-1"
        @keydown="onKeydown"
      >
        <button class="modal-shell__close" type="button" :aria-label="closeLabel ?? 'Close'" @click="close">
          x
        </button>
        <slot />
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-shell {
  position: fixed;
  z-index: 70;
  inset: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: oklch(0.14 0.006 110 / 42%);
  padding: 18px;
  backdrop-filter: blur(14px);
}

.modal-shell[data-tone="market"] {
  background:
    radial-gradient(circle at 20% 8%, oklch(0.62 0.14 205 / 18%), transparent 34%),
    radial-gradient(circle at 78% 12%, oklch(0.66 0.08 86 / 12%), transparent 30%),
    oklch(0.035 0.018 248 / 78%);
  backdrop-filter: blur(18px) saturate(1.12);
}

.modal-shell__panel {
  --modal-width: 720px;
  position: relative;
  display: grid;
  inline-size: min(var(--modal-width), calc(100vw - 36px));
  max-block-size: min(860px, calc(100dvh - 36px));
  overflow: hidden;
  border: 1px solid oklch(0.86 0.008 110 / 86%);
  border-radius: 12px;
  background: oklch(0.985 0.006 110);
  box-shadow: 0 30px 90px oklch(0.12 0.006 110 / 28%);
  color: oklch(0.17 0.004 110);
  outline: none;
  animation: modal-enter 180ms cubic-bezier(0.22, 1, 0.36, 1);
}

.modal-shell__panel[data-size="narrow"] {
  --modal-width: 540px;
}

.modal-shell__panel[data-size="wide"] {
  --modal-width: 1120px;
}

.modal-shell__panel[data-tone="market"] {
  border-color: oklch(0.72 0.105 205 / 28%);
  background:
    linear-gradient(145deg, oklch(0.1 0.026 242 / 94%), oklch(0.055 0.018 250 / 96%)),
    radial-gradient(circle at 16% 0%, oklch(0.72 0.12 205 / 16%), transparent 32%);
  box-shadow:
    0 32px 100px oklch(0.015 0.02 255 / 62%),
    0 0 72px oklch(0.64 0.13 205 / 10%),
    inset 0 1px 0 oklch(0.86 0.08 205 / 12%);
  color: oklch(0.94 0.018 215);
}

.modal-shell__close {
  position: absolute;
  z-index: 8;
  inset-block-start: 14px;
  inset-inline-end: 14px;
  display: inline-grid;
  inline-size: 36px;
  block-size: 36px;
  place-items: center;
  border: 1px solid oklch(0.82 0.006 110 / 86%);
  border-radius: 999px;
  background: oklch(0.985 0.006 110 / 86%);
  color: oklch(0.18 0.004 110);
  cursor: pointer;
  font: inherit;
  font-size: 18px;
  font-weight: 760;
  line-height: 1;
  backdrop-filter: blur(14px);
}

.modal-shell__close:hover,
.modal-shell__close:focus-visible {
  background: oklch(0.18 0.004 110);
  color: oklch(0.98 0.006 110);
}

.modal-shell__panel[data-tone="market"] .modal-shell__close {
  border-color: oklch(0.74 0.12 205 / 28%);
  background: oklch(0.09 0.022 245 / 72%);
  box-shadow: inset 0 1px 0 oklch(0.86 0.08 205 / 12%);
  color: oklch(0.9 0.07 205);
}

.modal-shell__panel[data-tone="market"] .modal-shell__close:hover,
.modal-shell__panel[data-tone="market"] .modal-shell__close:focus-visible {
  background: oklch(0.72 0.13 205);
  color: oklch(0.05 0.016 245);
}

@keyframes modal-enter {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.985);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 720px) {
  .modal-shell {
    align-items: end;
    padding: 8px;
  }

  .modal-shell__panel {
    inline-size: 100%;
    max-block-size: calc(100dvh - 16px);
    border-radius: 10px;
  }
}
</style>
