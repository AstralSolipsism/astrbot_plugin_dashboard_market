import { Mesh, Program, Renderer, Triangle } from 'ogl';

interface BalatroConsumer {
  active: boolean;
  canvas: HTMLCanvasElement;
  seed: number;
}

export interface BalatroConsumerSubscription {
  update: (options: Partial<Pick<BalatroConsumer, 'active' | 'seed'>>) => void;
  unregister: () => void;
}

const sourceWidth = 1280;
const sourceHeight = 800;
const maxActiveConsumers = 48;
const consumers = new Map<HTMLCanvasElement, BalatroConsumer>();

let animationFrameId = 0;
let mediaQuery: MediaQueryList | undefined;
let mesh: Mesh | undefined;
let program: Program | undefined;
let reducedMotion = false;
let renderer: Renderer | undefined;
let staticFrameScheduled = false;

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

export function registerBalatroConsumer(
  canvas: HTMLCanvasElement,
  options: Pick<BalatroConsumer, 'active' | 'seed'>
): BalatroConsumerSubscription {
  consumers.set(canvas, {
    canvas,
    active: options.active,
    seed: options.seed
  });
  syncRenderLoop();

  return {
    update(next) {
      const consumer = consumers.get(canvas);
      if (!consumer) {
        return;
      }
      if (next.active !== undefined) {
        consumer.active = next.active;
      }
      if (next.seed !== undefined) {
        consumer.seed = next.seed;
      }
      syncRenderLoop();
    },
    unregister() {
      consumers.delete(canvas);
      clearConsumerCanvas(canvas);
      if (consumers.size === 0) {
        destroyRenderer();
        return;
      }
      syncRenderLoop();
    }
  };
}

function syncRenderLoop(): void {
  removeDisconnectedConsumers();
  if (activeConsumers().length === 0) {
    stopAnimationLoop();
    return;
  }
  ensureRenderer();
  if (reducedMotion) {
    scheduleStaticFrame();
    return;
  }
  if (!animationFrameId) {
    animationFrameId = requestAnimationFrame(updateFrame);
  }
}

function ensureRenderer(): void {
  if (renderer && program && mesh) {
    return;
  }
  renderer = new Renderer({
    alpha: false,
    dpr: 1
  });
  const gl = renderer.gl;
  gl.clearColor(0, 0, 0, 1);
  renderer.setSize(sourceWidth, sourceHeight);

  const geometry = new Triangle(gl);
  program = new Program(gl, {
    vertex: vertexShader,
    fragment: fragmentShader,
    uniforms: {
      iTime: { value: 0 },
      iResolution: { value: [gl.canvas.width, gl.canvas.height, gl.canvas.width / gl.canvas.height] },
      uSpinRotation: { value: -2 },
      uSpinSpeed: { value: 7 },
      uOffset: { value: [0, 0] },
      uColor1: { value: hexToVec4('#06b6d4') },
      uColor2: { value: hexToVec4('#b8b096') },
      uColor3: { value: hexToVec4('#000000') },
      uContrast: { value: 8 },
      uLighting: { value: 0.4 },
      uSpinAmount: { value: 0.5 },
      uPixelFilter: { value: 2000 },
      uSpinEase: { value: 1 },
      uIsRotate: { value: false },
      uMouse: { value: [0.5, 0.5] }
    }
  });
  mesh = new Mesh(gl, { geometry, program });
  setupReducedMotionListener();
}

function setupReducedMotionListener(): void {
  if (mediaQuery || typeof window === 'undefined') {
    return;
  }
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  reducedMotion = mediaQuery.matches;
  mediaQuery.addEventListener('change', handleReducedMotionChange);
}

function destroyRenderer(): void {
  stopAnimationLoop();
  mediaQuery?.removeEventListener('change', handleReducedMotionChange);
  mediaQuery = undefined;
  renderer?.gl.getExtension('WEBGL_lose_context')?.loseContext();
  mesh = undefined;
  program = undefined;
  renderer = undefined;
  staticFrameScheduled = false;
}

function stopAnimationLoop(): void {
  if (!animationFrameId) {
    return;
  }
  cancelAnimationFrame(animationFrameId);
  animationFrameId = 0;
}

function scheduleStaticFrame(): void {
  if (staticFrameScheduled) {
    return;
  }
  staticFrameScheduled = true;
  requestAnimationFrame(() => {
    staticFrameScheduled = false;
    renderAndCopy(0);
  });
}

function updateFrame(time: number): void {
  animationFrameId = 0;
  if (activeConsumers().length === 0 || reducedMotion) {
    syncRenderLoop();
    return;
  }
  renderAndCopy(time * 0.001);
  animationFrameId = requestAnimationFrame(updateFrame);
}

function renderAndCopy(time: number): void {
  if (!renderer || !program || !mesh) {
    return;
  }
  program.uniforms.iTime.value = time;
  renderer.render({ scene: mesh });
  copyFrameToConsumers(renderer.gl.canvas);
}

function copyFrameToConsumers(source: HTMLCanvasElement): void {
  for (const consumer of activeConsumers()) {
    copyFrameToConsumer(source, consumer);
  }
}

function copyFrameToConsumer(source: HTMLCanvasElement, consumer: BalatroConsumer): void {
  const canvas = consumer.canvas;
  const rect = canvas.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return;
  }
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(rect.width * dpr));
  const height = Math.max(1, Math.round(rect.height * dpr));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const context = canvas.getContext('2d');
  if (!context) {
    return;
  }
  const cropWidth = Math.round(source.width * 0.68);
  const cropHeight = Math.round(source.height * 0.68);
  const cropX = Math.round(seedFraction(consumer.seed, 0) * Math.max(0, source.width - cropWidth));
  const cropY = Math.round(seedFraction(consumer.seed, 1) * Math.max(0, source.height - cropHeight));
  context.clearRect(0, 0, width, height);
  context.drawImage(source, cropX, cropY, cropWidth, cropHeight, 0, 0, width, height);
}

function activeConsumers(): BalatroConsumer[] {
  const viewportCenter = {
    x: window.innerWidth / 2,
    y: window.innerHeight / 2
  };
  return Array.from(consumers.values())
    .filter((consumer) => consumer.active && consumer.canvas.isConnected)
    .sort((a, b) => distanceToViewportCenter(a, viewportCenter) - distanceToViewportCenter(b, viewportCenter))
    .slice(0, maxActiveConsumers);
}

function distanceToViewportCenter(consumer: BalatroConsumer, viewportCenter: { x: number; y: number }): number {
  const rect = consumer.canvas.getBoundingClientRect();
  const x = rect.left + rect.width / 2 - viewportCenter.x;
  const y = rect.top + rect.height / 2 - viewportCenter.y;
  return x * x + y * y;
}

function removeDisconnectedConsumers(): void {
  for (const [canvas] of consumers) {
    if (!canvas.isConnected) {
      consumers.delete(canvas);
    }
  }
}

function clearConsumerCanvas(canvas: HTMLCanvasElement): void {
  const context = canvas.getContext('2d');
  context?.clearRect(0, 0, canvas.width, canvas.height);
}

function handleReducedMotionChange(event: MediaQueryListEvent): void {
  reducedMotion = event.matches;
  syncRenderLoop();
}

function seedFraction(seed: number, salt: number): number {
  const value = Math.sin((seed + 1) * (salt + 12.9898) * 78.233) * 43758.5453;
  return value - Math.floor(value);
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
