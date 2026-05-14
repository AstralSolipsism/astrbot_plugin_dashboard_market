import { computed, reactive, readonly, shallowRef } from 'vue';

interface DragState {
  pointerId: number;
  startX: number;
  startY: number;
  originX: number;
  originY: number;
  moved: boolean;
}

const interactiveSelector = 'a, button, input, textarea, select, [data-no-pan="true"]';

export function useInfiniteCanvas() {
  const pan = reactive({ x: 0, y: 0 });
  const isDragging = shallowRef(false);
  const suppressClickUntil = shallowRef(0);
  const drag = reactive<DragState>({
    pointerId: -1,
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0,
    moved: false
  });

  const planeStyle = computed<Record<string, string>>(() => ({
    '--pan-x': `${pan.x}px`,
    '--pan-y': `${pan.y}px`
  }));

  function isInteractiveTarget(target: EventTarget | null): boolean {
    return target instanceof Element && Boolean(target.closest(interactiveSelector));
  }

  function onPointerDown(event: PointerEvent): void {
    if (event.button !== 0 || isInteractiveTarget(event.target)) {
      return;
    }

    const target = event.currentTarget;
    if (!(target instanceof HTMLElement)) {
      return;
    }

    isDragging.value = true;
    drag.pointerId = event.pointerId;
    drag.startX = event.clientX;
    drag.startY = event.clientY;
    drag.originX = pan.x;
    drag.originY = pan.y;
    drag.moved = false;
    target.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: PointerEvent): void {
    if (!isDragging.value || event.pointerId !== drag.pointerId) {
      return;
    }

    event.preventDefault();
    const moveX = event.clientX - drag.startX;
    const moveY = event.clientY - drag.startY;
    if (Math.hypot(moveX, moveY) > 4) {
      drag.moved = true;
    }

    pan.x = drag.originX + moveX;
    pan.y = drag.originY + moveY;
  }

  function onPointerUp(event: PointerEvent): void {
    if (event.pointerId !== drag.pointerId) {
      return;
    }

    const target = event.currentTarget;
    if (target instanceof HTMLElement && target.hasPointerCapture(event.pointerId)) {
      target.releasePointerCapture(event.pointerId);
    }

    if (drag.moved) {
      suppressClickUntil.value = performance.now() + 120;
    }

    isDragging.value = false;
    drag.pointerId = -1;
  }

  function onWheel(event: WheelEvent): void {
    if (isInteractiveTarget(event.target)) {
      return;
    }

    event.preventDefault();
    pan.x -= event.deltaX;
    pan.y -= event.deltaY;
  }

  function resetPan(): void {
    pan.x = 0;
    pan.y = 0;
  }

  function shouldSuppressClick(): boolean {
    return performance.now() < suppressClickUntil.value;
  }

  return {
    isDragging: readonly(isDragging),
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onWheel,
    planeStyle,
    resetPan,
    shouldSuppressClick
  };
}
