<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, useTemplateRef, watch } from 'vue';
import { registerBalatroConsumer, type BalatroConsumerSubscription } from './balatroFrameSource';

const props = withDefaults(
  defineProps<{
    active?: boolean;
    color1?: string;
    color2?: string;
    color3?: string;
    seed?: number;
  }>(),
  {
    active: false,
    color1: '#06b6d4',
    color2: '#b8b096',
    color3: '#000000',
    seed: 1
  }
);

const canvasRef = useTemplateRef<HTMLCanvasElement>('canvas');
let subscription: BalatroConsumerSubscription | undefined;

const backdropStyle = computed(() => ({
  '--balatro-color-1': props.color1,
  '--balatro-color-2': props.color2,
  '--balatro-color-3': props.color3
}));

onMounted(() => {
  if (!canvasRef.value) {
    return;
  }
  subscription = registerBalatroConsumer(canvasRef.value, {
    active: props.active,
    seed: props.seed
  });
});

onBeforeUnmount(() => {
  subscription?.unregister();
});

watch(
  () => [props.active, props.seed],
  () => {
    subscription?.update({
      active: props.active,
      seed: props.seed
    });
  }
);
</script>

<template>
  <div
    class="balatro-backdrop"
    :style="backdropStyle"
    aria-hidden="true"
  >
    <div class="balatro-backdrop__fallback"></div>
    <canvas ref="canvas" class="balatro-backdrop__canvas"></canvas>
  </div>
</template>

<style scoped>
.balatro-backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: var(--balatro-color-3);
  opacity: 0.6;
  pointer-events: none;
  -webkit-mask-image:
    linear-gradient(to right, transparent 0, #000 7%, #000 93%, transparent 100%),
    linear-gradient(to bottom, transparent 0, #000 8%, #000 92%, transparent 100%);
  -webkit-mask-composite: source-in;
  mask-image:
    linear-gradient(to right, transparent 0, #000 7%, #000 93%, transparent 100%),
    linear-gradient(to bottom, transparent 0, #000 8%, #000 92%, transparent 100%);
  mask-composite: intersect;
}

.balatro-backdrop__fallback,
.balatro-backdrop__canvas {
  position: absolute;
  inset: 0;
  display: block;
  inline-size: 100%;
  block-size: 100%;
}

.balatro-backdrop__fallback {
  inset: -18%;
  background:
    radial-gradient(circle at 22% 18%, color-mix(in oklab, var(--balatro-color-1) 64%, oklch(0.08 0.032 245) 36%) 0 12%, transparent 35%),
    radial-gradient(circle at 74% 32%, color-mix(in oklab, var(--balatro-color-2) 42%, oklch(0.06 0.018 250) 58%) 0 14%, transparent 34%),
    radial-gradient(circle at 44% 82%, color-mix(in oklab, var(--balatro-color-1) 42%, var(--balatro-color-3) 58%) 0 18%, transparent 40%),
    conic-gradient(from 228deg at 50% 50%, var(--balatro-color-3), color-mix(in oklab, var(--balatro-color-1) 62%, var(--balatro-color-3) 38%), color-mix(in oklab, var(--balatro-color-2) 36%, var(--balatro-color-3) 64%), var(--balatro-color-3));
  filter: brightness(0.72) saturate(1.12) contrast(1.14);
}

.balatro-backdrop::after {
  position: absolute;
  z-index: 2;
  inset: 0;
  background:
    radial-gradient(circle at 48% 42%, transparent 0 36%, oklch(0.04 0.024 250 / 42%) 78%),
    linear-gradient(135deg, oklch(0.03 0.02 250 / 22%), oklch(0.12 0.05 220 / 12%) 48%, oklch(0.02 0.018 260 / 38%));
  content: '';
  mix-blend-mode: multiply;
}

.balatro-backdrop__canvas {
  z-index: 1;
  filter: brightness(0.68) saturate(1.12) contrast(1.14);
}

</style>
