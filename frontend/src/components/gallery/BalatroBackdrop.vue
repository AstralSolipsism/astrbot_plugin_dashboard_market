<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useTemplateRef, watch } from 'vue';
import { Mesh, Program, Renderer, Triangle } from 'ogl';

const props = withDefaults(
  defineProps<{
    active?: boolean;
    color1?: string;
    color2?: string;
    color3?: string;
    contrast?: number;
    isRotate?: boolean;
    lighting?: number;
    mouseInteraction?: boolean;
    offset?: [number, number];
    pixelFilter?: number;
    spinAmount?: number;
    spinEase?: number;
    spinRotation?: number;
    spinSpeed?: number;
  }>(),
  {
    active: false,
    color1: '#181e57',
    color2: '#03030a',
    color3: '#5a273f',
    contrast: 3.5,
    isRotate: false,
    lighting: 0.4,
    mouseInteraction: true,
    offset: () => [0, 0],
    pixelFilter: 700,
    spinAmount: 0.25,
    spinEase: 1,
    spinRotation: -2,
    spinSpeed: 7
  }
);

const containerRef = useTemplateRef<HTMLDivElement>('container');
const reducedMotion = ref(false);

let animationFrameId = 0;
let mediaQuery: MediaQueryList | undefined;
let mesh: Mesh | undefined;
let program: Program | undefined;
let renderer: Renderer | undefined;
let resizeObserver: ResizeObserver | undefined;

const backdropStyle = computed(() => ({
  '--balatro-color-1': props.color1,
  '--balatro-color-2': props.color2,
  '--balatro-color-3': props.color3
}));

const vertexShader = `
attribute vec2 uv;
attribute vec2 position;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0, 1);
}
`;

const fragmentShader = `
precision highp float;

uniform float iTime;
uniform vec3 iResolution;
uniform float uSpinRotation;
uniform float uSpinSpeed;
uniform vec2 uOffset;
uniform vec4 uColor1;
uniform vec4 uColor2;
uniform vec4 uColor3;
uniform float uContrast;
uniform float uLighting;
uniform float uSpinAmount;
uniform float uPixelFilter;
uniform float uSpinEase;
uniform bool uIsRotate;
uniform vec2 uMouse;

varying vec2 vUv;

vec4 effect(vec2 screenSize, vec2 screenCoords) {
  float pixelSize = length(screenSize.xy) / uPixelFilter;
  vec2 uv = (floor(screenCoords.xy * (1.0 / pixelSize)) * pixelSize - 0.5 * screenSize.xy) / length(screenSize.xy) - uOffset;
  float uvLen = length(uv);

  float speed = (uSpinRotation * uSpinEase * 0.2);
  if (uIsRotate) {
    speed = iTime * speed;
  }
  speed += 302.2;

  float mouseInfluence = (uMouse.x * 2.0 - 1.0);
  speed += mouseInfluence * 0.1;

  float newPixelAngle = atan(uv.y, uv.x) + speed - uSpinEase * 20.0 * (uSpinAmount * uvLen + (1.0 - uSpinAmount));
  vec2 mid = (screenSize.xy / length(screenSize.xy)) / 2.0;
  uv = (vec2(uvLen * cos(newPixelAngle) + mid.x, uvLen * sin(newPixelAngle) + mid.y) - mid);

  uv *= 30.0;
  float baseSpeed = iTime * uSpinSpeed;
  speed = baseSpeed + mouseInfluence * 2.0;

  vec2 uv2 = vec2(uv.x + uv.y);

  for (int i = 0; i < 5; i++) {
    uv2 += sin(max(uv.x, uv.y)) + uv;
    uv += 0.5 * vec2(
      cos(5.1123314 + 0.353 * uv2.y + speed * 0.131121),
      sin(uv2.x - 0.113 * speed)
    );
    uv -= cos(uv.x + uv.y) - sin(uv.x * 0.711 - uv.y);
  }

  float contrastMod = (0.25 * uContrast + 0.5 * uSpinAmount + 1.2);
  float paintRes = min(2.0, max(0.0, length(uv) * 0.035 * contrastMod));
  float c1p = max(0.0, 1.0 - contrastMod * abs(1.0 - paintRes));
  float c2p = max(0.0, 1.0 - contrastMod * abs(paintRes));
  float c3p = 1.0 - min(1.0, c1p + c2p);
  float light = (uLighting - 0.2) * max(c1p * 5.0 - 4.0, 0.0) + uLighting * max(c2p * 5.0 - 4.0, 0.0);

  return (0.3 / uContrast) * uColor1 + (1.0 - 0.3 / uContrast) * (uColor1 * c1p + uColor2 * c2p + vec4(c3p * uColor3.rgb, c3p * uColor1.a)) + light;
}

void main() {
  vec2 uv = vUv * iResolution.xy;
  gl_FragColor = effect(iResolution.xy, uv);
}
`;

onMounted(() => {
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  reducedMotion.value = mediaQuery.matches;
  mediaQuery.addEventListener('change', handleReducedMotionChange);
  restartRenderer();
});

onBeforeUnmount(() => {
  mediaQuery?.removeEventListener('change', handleReducedMotionChange);
  destroyRenderer();
});

watch(
  () => [
    props.active,
    props.color1,
    props.color2,
    props.color3,
    props.contrast,
    props.isRotate,
    props.lighting,
    props.mouseInteraction,
    props.offset[0],
    props.offset[1],
    props.pixelFilter,
    props.spinAmount,
    props.spinEase,
    props.spinRotation,
    props.spinSpeed,
    reducedMotion.value
  ],
  () => restartRenderer(),
  { flush: 'post' }
);

function restartRenderer(): void {
  destroyRenderer();
  if (!props.active || !containerRef.value) {
    return;
  }

  const container = containerRef.value;
  renderer = new Renderer({
    alpha: false,
    dpr: Math.min(window.devicePixelRatio || 1, 2)
  });
  const gl = renderer.gl;
  gl.clearColor(0, 0, 0, 1);
  gl.canvas.className = 'balatro-backdrop__canvas';
  gl.canvas.style.position = 'absolute';
  gl.canvas.style.inset = '0';
  gl.canvas.style.width = '100%';
  gl.canvas.style.height = '100%';
  gl.canvas.style.display = 'block';
  gl.canvas.style.pointerEvents = 'none';

  const geometry = new Triangle(gl);
  program = new Program(gl, {
    vertex: vertexShader,
    fragment: fragmentShader,
    uniforms: {
      iTime: { value: 0 },
      iResolution: { value: [1, 1, 1] },
      uSpinRotation: { value: props.spinRotation },
      uSpinSpeed: { value: props.spinSpeed },
      uOffset: { value: props.offset },
      uColor1: { value: hexToVec4(props.color1) },
      uColor2: { value: hexToVec4(props.color2) },
      uColor3: { value: hexToVec4(props.color3) },
      uContrast: { value: props.contrast },
      uLighting: { value: props.lighting },
      uSpinAmount: { value: props.spinAmount },
      uPixelFilter: { value: props.pixelFilter },
      uSpinEase: { value: props.spinEase },
      uIsRotate: { value: props.isRotate && !reducedMotion.value },
      uMouse: { value: [0.5, 0.5] }
    }
  });
  mesh = new Mesh(gl, { geometry, program });

  container.appendChild(gl.canvas);
  resizeRenderer();
  resizeObserver = new ResizeObserver(resizeRenderer);
  resizeObserver.observe(container);
  container.addEventListener('mousemove', handleMouseMove);

  if (reducedMotion.value) {
    renderFrame(0);
    return;
  }
  animationFrameId = requestAnimationFrame(updateFrame);
}

function destroyRenderer(): void {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = 0;
  }
  resizeObserver?.disconnect();
  resizeObserver = undefined;

  const container = containerRef.value;
  if (container) {
    container.removeEventListener('mousemove', handleMouseMove);
  }

  const canvas = renderer?.gl.canvas;
  if (canvas?.parentNode) {
    canvas.parentNode.removeChild(canvas);
  }
  renderer?.gl.getExtension('WEBGL_lose_context')?.loseContext();
  mesh = undefined;
  program = undefined;
  renderer = undefined;
}

function resizeRenderer(): void {
  const container = containerRef.value;
  if (!container || !renderer || !program) {
    return;
  }
  renderer.setSize(Math.max(1, container.offsetWidth), Math.max(1, container.offsetHeight));
  const gl = renderer.gl;
  program.uniforms.iResolution.value = [gl.canvas.width, gl.canvas.height, gl.canvas.width / gl.canvas.height];
  if (reducedMotion.value) {
    renderFrame(0);
  }
}

function updateFrame(time: number): void {
  animationFrameId = requestAnimationFrame(updateFrame);
  renderFrame(time * 0.001);
}

function renderFrame(time: number): void {
  if (!renderer || !program || !mesh) {
    return;
  }
  program.uniforms.iTime.value = time;
  renderer.render({ scene: mesh });
}

function handleMouseMove(event: MouseEvent): void {
  if (!program || !props.mouseInteraction || reducedMotion.value) {
    return;
  }
  const container = containerRef.value;
  if (!container) {
    return;
  }
  const rect = container.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return;
  }
  const x = (event.clientX - rect.left) / rect.width;
  const y = 1 - (event.clientY - rect.top) / rect.height;
  program.uniforms.uMouse.value = [x, y];
}

function handleReducedMotionChange(event: MediaQueryListEvent): void {
  reducedMotion.value = event.matches;
}

function hexToVec4(hex: string): [number, number, number, number] {
  const hexStr = hex.replace('#', '');
  if (!/^[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(hexStr)) {
    return [1, 1, 1, 1];
  }
  const r = Number.parseInt(hexStr.slice(0, 2), 16) / 255;
  const g = Number.parseInt(hexStr.slice(2, 4), 16) / 255;
  const b = Number.parseInt(hexStr.slice(4, 6), 16) / 255;
  const a = hexStr.length === 8 ? Number.parseInt(hexStr.slice(6, 8), 16) / 255 : 1;
  return [r, g, b, a];
}
</script>

<template>
  <div ref="container" class="balatro-backdrop" :style="backdropStyle" aria-hidden="true">
    <div class="balatro-backdrop__fallback"></div>
  </div>
</template>

<style scoped>
.balatro-backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: var(--balatro-color-2);
}

.balatro-backdrop__fallback {
  position: absolute;
  inset: -18%;
  background:
    radial-gradient(circle at 24% 20%, color-mix(in oklab, var(--balatro-color-1) 84%, white 16%) 0 13%, transparent 34%),
    radial-gradient(circle at 72% 34%, var(--balatro-color-3) 0 12%, transparent 31%),
    radial-gradient(circle at 44% 82%, color-mix(in oklab, var(--balatro-color-1) 52%, var(--balatro-color-2) 48%) 0 16%, transparent 38%),
    linear-gradient(132deg, var(--balatro-color-2), color-mix(in oklab, var(--balatro-color-1) 36%, var(--balatro-color-2) 64%) 48%, var(--balatro-color-3));
  filter: saturate(1.08) contrast(1.08);
}

:deep(.balatro-backdrop__canvas) {
  z-index: 1;
}
</style>
