import type { Action } from 'svelte/action';

export const masonryItem: Action<HTMLElement> = (node) => {
  const update = () => {
    const inner = node.firstElementChild as HTMLElement | null;
    if (!inner) return;
    const styles = getComputedStyle(node.parentElement ?? node);
    const row = Number.parseFloat(styles.getPropertyValue('grid-auto-rows')) || 8;
    const gap = Number.parseFloat(styles.rowGap) || 16;
    const height = inner.getBoundingClientRect().height;
    node.style.gridRowEnd = `span ${Math.ceil((height + gap) / (row + gap))}`;
  };

  const observer = new ResizeObserver(update);
  const inner = node.firstElementChild;
  if (inner) observer.observe(inner);
  requestAnimationFrame(update);

  return {
    update,
    destroy() {
      observer.disconnect();
    },
  };
};
