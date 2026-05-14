<script setup lang="ts">
import { Mesh, Program, Renderer, Triangle } from 'ogl';
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue';

const props = withDefaults(
  defineProps<{
    autoCenterRepulsion?: number;
    density?: number;
    disableAnimation?: boolean;
    focal?: [number, number];
    glowIntensity?: number;
    hueShift?: number;
    mouseInteraction?: boolean;
    mouseRepulsion?: boolean;
    repulsionStrength?: number;
    rotation?: [number, number];
    rotationSpeed?: number;
    saturation?: number;
    speed?: number;
    starSpeed?: number;
    transparent?: boolean;
    twinkleIntensity?: number;
  }>(),
  {
    autoCenterRepulsion: 0,
    density: 1,
    disableAnimation: false,
    focal: () => [0.5, 0.5],
    glowIntensity: 0.3,
    hueShift: 140,
    mouseInteraction: true,
    mouseRepulsion: true,
    repulsionStrength: 2,
    rotation: () => [1, 0],
    rotationSpeed: 0.1,
    saturation: 0,
    speed: 1,
    starSpeed: 0.5,
    transparent: true,
    twinkleIntensity: 0.3
  }
);

const containerRef = useTemplateRef<HTMLElement>('container');

let animationFrameId = 0;
let mediaQuery: MediaQueryList | undefined;
let mesh: Mesh | undefined;
let program: Program | undefined;
let renderer: Renderer | undefined;
let resizeObserver: ResizeObserver | undefined;

const targetMousePos = { x: 0.5, y: 0.5 };
const smoothMousePos = { x: 0.5, y: 0.5 };
let targetMouseActive = 0;
let smoothMouseActive = 0;

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

uniform float uTime;
uniform vec3 uResolution;
uniform vec2 uFocal;
uniform vec2 uRotation;
uniform float uStarSpeed;
uniform float uDensity;
uniform float uHueShift;
uniform float uSpeed;
uniform vec2 uMouse;
uniform float uGlowIntensity;
uniform float uSaturation;
uniform bool uMouseRepulsion;
uniform float uTwinkleIntensity;
uniform float uRotationSpeed;
uniform float uRepulsionStrength;
uniform float uMouseActiveFactor;
uniform float uAutoCenterRepulsion;
uniform bool uTransparent;

varying vec2 vUv;

#define NUM_LAYER 4.0
#define STAR_COLOR_CUTOFF 0.2
#define MAT45 mat2(0.7071, -0.7071, 0.7071, 0.7071)
#define PERIOD 3.0

float Hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float tri(float x) {
  return abs(fract(x) * 2.0 - 1.0);
}

float tris(float x) {
  float t = fract(x);
  return 1.0 - smoothstep(0.0, 1.0, abs(2.0 * t - 1.0));
}

float trisn(float x) {
  float t = fract(x);
  return 2.0 * (1.0 - smoothstep(0.0, 1.0, abs(2.0 * t - 1.0))) - 1.0;
}

vec3 hsv2rgb(vec3 c) {
  vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float Star(vec2 uv, float flare) {
  float d = length(uv);
  float m = (0.05 * uGlowIntensity) / d;
  float rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * flare * uGlowIntensity;
  uv *= MAT45;
  rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * 0.3 * flare * uGlowIntensity;
  m *= smoothstep(1.0, 0.2, d);
  return m;
}

vec3 StarLayer(vec2 uv) {
  vec3 col = vec3(0.0);
  vec2 gv = fract(uv) - 0.5;
  vec2 id = floor(uv);

  for (int y = -1; y <= 1; y++) {
    for (int x = -1; x <= 1; x++) {
      vec2 offset = vec2(float(x), float(y));
      vec2 si = id + vec2(float(x), float(y));
      float seed = Hash21(si);
      float size = fract(seed * 345.32);
      float glossLocal = tri(uStarSpeed / (PERIOD * seed + 1.0));
      float flareSize = smoothstep(0.9, 1.0, size) * glossLocal;

      float red = smoothstep(STAR_COLOR_CUTOFF, 1.0, Hash21(si + 1.0)) + STAR_COLOR_CUTOFF;
      float blu = smoothstep(STAR_COLOR_CUTOFF, 1.0, Hash21(si + 3.0)) + STAR_COLOR_CUTOFF;
      float grn = min(red, blu) * seed;
      vec3 base = vec3(red, grn, blu);

      float hue = atan(base.g - base.r, base.b - base.r) / (2.0 * 3.14159) + 0.5;
      hue = fract(hue + uHueShift / 360.0);
      float sat = length(base - vec3(dot(base, vec3(0.299, 0.587, 0.114)))) * uSaturation;
      float val = max(max(base.r, base.g), base.b);
      base = hsv2rgb(vec3(hue, sat, val));

      vec2 pad = vec2(tris(seed * 34.0 + uTime * uSpeed / 10.0), tris(seed * 38.0 + uTime * uSpeed / 30.0)) - 0.5;
      float star = Star(gv - offset - pad, flareSize);
      float twinkle = trisn(uTime * uSpeed + seed * 6.2831) * 0.5 + 1.0;
      twinkle = mix(1.0, twinkle, uTwinkleIntensity);
      star *= twinkle;
      col += star * size * base;
    }
  }

  return col;
}

void main() {
  vec2 focalPx = uFocal * uResolution.xy;
  vec2 uv = (vUv * uResolution.xy - focalPx) / uResolution.y;
  vec2 mouseNorm = uMouse - vec2(0.5);

  if (uAutoCenterRepulsion > 0.0) {
    vec2 centerUV = vec2(0.0, 0.0);
    float centerDist = length(uv - centerUV);
    vec2 repulsion = normalize(uv - centerUV) * (uAutoCenterRepulsion / (centerDist + 0.1));
    uv += repulsion * 0.05;
  } else if (uMouseRepulsion) {
    vec2 mousePosUV = (uMouse * uResolution.xy - focalPx) / uResolution.y;
    float mouseDist = length(uv - mousePosUV);
    vec2 repulsion = normalize(uv - mousePosUV) * (uRepulsionStrength / (mouseDist + 0.1));
    uv += repulsion * 0.05 * uMouseActiveFactor;
  } else {
    vec2 mouseOffset = mouseNorm * 0.1 * uMouseActiveFactor;
    uv += mouseOffset;
  }

  float autoRotAngle = uTime * uRotationSpeed;
  mat2 autoRot = mat2(cos(autoRotAngle), -sin(autoRotAngle), sin(autoRotAngle), cos(autoRotAngle));
  uv = autoRot * uv;
  uv = mat2(uRotation.x, -uRotation.y, uRotation.y, uRotation.x) * uv;

  vec3 col = vec3(0.0);
  for (float i = 0.0; i < 1.0; i += 1.0 / NUM_LAYER) {
    float depth = fract(i + uStarSpeed * uSpeed);
    float scale = mix(20.0 * uDensity, 0.5 * uDensity, depth);
    float fade = depth * smoothstep(1.0, 0.9, depth);
    col += StarLayer(uv * scale + i * 453.32) * fade;
  }

  if (uTransparent) {
    float alpha = length(col);
    alpha = smoothstep(0.0, 0.3, alpha);
    alpha = min(alpha, 1.0);
    gl_FragColor = vec4(col, alpha);
  } else {
    gl_FragColor = vec4(col, 1.0);
  }
}
`;

onMounted(() => {
  const container = containerRef.value;
  if (!container) {
    return;
  }

  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  renderer = new Renderer({
    alpha: props.transparent,
    dpr: Math.min(window.devicePixelRatio || 1, 1.5),
    premultipliedAlpha: false
  });
  const gl = renderer.gl;

  if (props.transparent) {
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.clearColor(0, 0, 0, 0);
  } else {
    gl.clearColor(0, 0, 0, 1);
  }

  const geometry = new Triangle(gl);
  program = new Program(gl, {
    vertex: vertexShader,
    fragment: fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: [1, 1, 1] },
      uFocal: { value: new Float32Array(props.focal) },
      uRotation: { value: new Float32Array(props.rotation) },
      uStarSpeed: { value: props.starSpeed },
      uDensity: { value: props.density },
      uHueShift: { value: props.hueShift },
      uSpeed: { value: props.speed },
      uMouse: { value: new Float32Array([smoothMousePos.x, smoothMousePos.y]) },
      uGlowIntensity: { value: props.glowIntensity },
      uSaturation: { value: props.saturation },
      uMouseRepulsion: { value: props.mouseRepulsion },
      uTwinkleIntensity: { value: props.twinkleIntensity },
      uRotationSpeed: { value: props.rotationSpeed },
      uRepulsionStrength: { value: props.repulsionStrength },
      uMouseActiveFactor: { value: 0 },
      uAutoCenterRepulsion: { value: props.autoCenterRepulsion },
      uTransparent: { value: props.transparent }
    }
  });
  mesh = new Mesh(gl, { geometry, program });
  container.appendChild(gl.canvas);

  resize();
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
  }
  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', handleMouseMove);
  window.addEventListener('mouseout', handleMouseOut);
  animationFrameId = requestAnimationFrame(update);
});

onBeforeUnmount(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
  resizeObserver?.disconnect();
  window.removeEventListener('resize', resize);
  window.removeEventListener('mousemove', handleMouseMove);
  window.removeEventListener('mouseout', handleMouseOut);
  renderer?.gl.canvas.remove();
  renderer?.gl.getExtension('WEBGL_lose_context')?.loseContext();
  mesh = undefined;
  program = undefined;
  renderer = undefined;
});

function resize(): void {
  const container = containerRef.value;
  if (!container || !renderer || !program) {
    return;
  }
  const width = Math.max(1, container.offsetWidth);
  const height = Math.max(1, container.offsetHeight);
  renderer.setSize(width, height);
  program.uniforms.uResolution.value = [renderer.gl.canvas.width, renderer.gl.canvas.height, width / height];
}

function update(time: number): void {
  animationFrameId = requestAnimationFrame(update);
  if (!renderer || !program || !mesh) {
    return;
  }

  const animationDisabled = props.disableAnimation || Boolean(mediaQuery?.matches);
  if (!animationDisabled) {
    program.uniforms.uTime.value = time * 0.001;
    program.uniforms.uStarSpeed.value = (time * 0.001 * props.starSpeed) / 10;
  }

  const lerpFactor = 0.05;
  smoothMousePos.x += (targetMousePos.x - smoothMousePos.x) * lerpFactor;
  smoothMousePos.y += (targetMousePos.y - smoothMousePos.y) * lerpFactor;
  smoothMouseActive += (targetMouseActive - smoothMouseActive) * lerpFactor;

  program.uniforms.uMouse.value[0] = smoothMousePos.x;
  program.uniforms.uMouse.value[1] = smoothMousePos.y;
  program.uniforms.uMouseActiveFactor.value = animationDisabled ? 0 : smoothMouseActive;
  renderer.render({ scene: mesh });
}

function handleMouseMove(event: MouseEvent): void {
  const container = containerRef.value;
  if (!container || !props.mouseInteraction) {
    return;
  }
  const rect = container.getBoundingClientRect();
  if (
    event.clientX < rect.left ||
    event.clientX > rect.right ||
    event.clientY < rect.top ||
    event.clientY > rect.bottom
  ) {
    targetMouseActive = 0;
    return;
  }
  targetMousePos.x = (event.clientX - rect.left) / rect.width;
  targetMousePos.y = 1 - (event.clientY - rect.top) / rect.height;
  targetMouseActive = 1;
}

function handleMouseOut(event: MouseEvent): void {
  if (!event.relatedTarget) {
    targetMouseActive = 0;
  }
}
</script>

<template>
  <div ref="container" class="galaxy-backdrop" aria-hidden="true"></div>
</template>

<style scoped>
.galaxy-backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 48%, oklch(0.23 0.062 220 / 58%), transparent 44%),
    radial-gradient(circle at 18% 22%, oklch(0.38 0.096 214 / 38%), transparent 32%),
    radial-gradient(circle at 78% 72%, oklch(0.32 0.07 88 / 30%), transparent 36%),
    linear-gradient(135deg, oklch(0.08 0.024 250), oklch(0.11 0.018 214) 44%, oklch(0.07 0.015 260));
  pointer-events: none;
}

.galaxy-backdrop :deep(canvas) {
  display: block;
  inline-size: 100%;
  block-size: 100%;
}
</style>
