<script setup lang="ts">
import { nextTick, onBeforeUnmount, shallowRef, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    ariaLabel?: string;
    closeLabel?: string;
    labelledBy?: string;
    open: boolean;
    size?: 'narrow' | 'medium' | 'wide';
  }>(),
  {
    size: 'medium'
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
    <div v-if="open" class="modal-shell" data-no-pan="true" @click.self="close">
      <section
        ref="panel"
        class="modal-shell__panel"
        :aria-label="ariaLabel"
        :aria-labelledby="labelledBy"
        aria-modal="true"
        :data-size="size"
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
