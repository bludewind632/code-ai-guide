'use client';

import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

export default function MermaidView({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'default' });
    async function render() {
      if (!ref.current || !chart) return;
      const id = `mermaid-${Math.random().toString(36).slice(2)}`;
      try {
        const { svg } = await mermaid.render(id, chart);
        ref.current.innerHTML = svg;
      } catch (e) {
        ref.current.innerHTML = `<pre>${chart}</pre>`;
      }
    }
    render();
  }, [chart]);

  return <div ref={ref} />;
}
