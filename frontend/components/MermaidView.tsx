'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';

function parseSvgSize(svg: string): { w: number; h: number } {
  const match = svg.match(/viewBox="([^"]+)"/);
  if (match) {
    const parts = match[1].split(/\s+/).map(Number);
    return { w: parts[2] || 800, h: parts[3] || 600 };
  }
  const w = Number(svg.match(/width="(\d+)"/)?.[1]) || 800;
  const h = Number(svg.match(/height="(\d+)"/)?.[1]) || 600;
  return { w, h };
}

export default function MermaidView({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const areaRef = useRef<HTMLDivElement>(null);
  const [zoomed, setZoomed] = useState(false);
  const [svgContent, setSvgContent] = useState('');
  const [svgSize, setSvgSize] = useState({ w: 800, h: 600 });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0, px: 0, py: 0 });

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'Arial, Helvetica, sans-serif',
    });

    async function render() {
      if (!ref.current || !chart) return;
      ref.current.innerHTML = '';

      const id = `mermaid-${Math.random().toString(36).slice(2)}`;
      try {
        const { svg } = await mermaid.render(id, chart);
        ref.current.innerHTML = svg;
        setSvgContent(svg);
        setSvgSize(parseSvgSize(svg));
      } catch (e) {
        console.error('Mermaid render error:', e);
        ref.current.innerHTML = `<pre class="mermaid-error">${chart}</pre>`;
      }
    }

    render();
  }, [chart]);

  const close = useCallback(() => { setZoomed(false); setPanX(0); setPanY(0); }, []);

  // ── 弹层尺寸和初始缩放 ──
  const PAD_X = 64;
  const PAD_Y = 88;
  // 弹窗始终撑满屏幕
  const modalW = window.innerWidth * 0.80;
  const modalH = window.innerHeight * 0.80;
  // 内容可用区域
  const contentW = modalW - PAD_X;
  const contentH = modalH - PAD_Y;
  // 图去适配弹窗：计算恰好填满内容区的缩放倍率，上限 3.5 倍
  const fillZoom = Math.min(contentW / svgSize.w, contentH / svgSize.h) * 0.9;
  const initialZoom = Math.max(0.3, Math.min(2.0, +fillZoom.toFixed(1)));

  // ── 缩放控制 ──
  const ZOOM_STEP = 0.1;
  const ZOOM_MIN = 0.3;
  const ZOOM_MAX = 6;

  const applyZoom = useCallback((newZoom: number, cx?: number, cy?: number) => {
    const clamped = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, +newZoom.toFixed(2)));
    if (cx !== undefined && cy !== undefined) {
      const ratio = clamped / zoomLevel;
      setPanX((px) => cx - ratio * (cx - px));
      setPanY((py) => cy - ratio * (cy - py));
    }
    setZoomLevel(clamped);
  }, [zoomLevel]);

  const zoomIn = useCallback(() => applyZoom(zoomLevel + ZOOM_STEP), [applyZoom, zoomLevel]);
  const zoomOut = useCallback(() => applyZoom(zoomLevel - ZOOM_STEP), [applyZoom, zoomLevel]);
  const zoomReset = useCallback(() => { setZoomLevel(initialZoom); setPanX(0); setPanY(0); }, [initialZoom]);

  // ── 滚轮缩放（以鼠标位置为中心）──
  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const rect = areaRef.current?.getBoundingClientRect();
    if (!rect) return;
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
    applyZoom(zoomLevel + delta, cx, cy);
  }, [applyZoom, zoomLevel]);

  // ── 鼠标拖拽 ──
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    e.preventDefault();
    dragging.current = true;
    dragStart.current = { x: e.clientX, y: e.clientY, px: panX, py: panY };
  }, [panX, panY]);

  useEffect(() => {
    if (!zoomed) return;
    const onMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      setPanX(dragStart.current.px + e.clientX - dragStart.current.x);
      setPanY(dragStart.current.py + e.clientY - dragStart.current.y);
    };
    const onUp = () => { dragging.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [zoomed]);

  useEffect(() => {
    if (!zoomed) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [zoomed, close]);

  function openZoomed() {
    if (!svgContent) return;
    setZoomLevel(initialZoom);
    setPanX(0);
    setPanY(0);
    setZoomed(true);
  }

  return (
    <>
      <div
        ref={ref}
        className="mermaid-container"
        onClick={openZoomed}
        style={{ cursor: svgContent ? 'zoom-in' : 'default' }}
      />
      {zoomed && (
        <div className="mermaid-overlay" onClick={close}>
          <div
            className="mermaid-zoomed"
            style={{ width: modalW, height: modalH }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mermaid-zoom-controls">
              <button className="mermaid-zoom-btn" onClick={zoomOut} title="缩小 (滚轮向下)">−</button>
              <span className="mermaid-zoom-label" onClick={zoomReset} title="点击重置">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button className="mermaid-zoom-btn" onClick={zoomIn} title="放大 (滚轮向上)">+</button>
              <div className="mermaid-zoom-divider" />
              <button className="mermaid-close" onClick={close} title="关闭 (Esc)">✕</button>
            </div>
            <div
              ref={areaRef}
              className="mermaid-zoom-area"
              onWheel={onWheel}
              onMouseDown={onMouseDown}
              style={{ cursor: 'grab' }}
            >
              <div
                className="mermaid-zoom-content"
                style={{
                  width: svgSize.w * zoomLevel,
                  height: svgSize.h * zoomLevel,
                  transform: `translate(${panX}px, ${panY}px)`,
                }}
              >
                <div
                  style={{
                    transform: `scale(${zoomLevel})`,
                    transformOrigin: '0 0',
                    width: svgSize.w,
                    height: svgSize.h,
                  }}
                  dangerouslySetInnerHTML={{ __html: svgContent }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
