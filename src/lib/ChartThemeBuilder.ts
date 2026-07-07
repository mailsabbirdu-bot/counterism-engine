import { Easing } from 'remotion';

export const ChartThemeBuilder = (overlay: any, personality: any) => {
    const font = overlay.font || 'Inter, sans-serif';
    return {
        theme: {
            axis: {
                ticks: { text: { fill: '#ffffff80', fontSize: 16, fontFamily: font, fontWeight: 'bold' } },
                legend: { text: { fill: '#ffffffe0', fontSize: 20, fontFamily: font, fontWeight: '900' } }
            },
            grid: { line: { stroke: 'rgba(255,255,255,0.05)', strokeWidth: personality.grid ? 1 : 0 } },
            tooltip: { container: { background: '#09090b', color: '#fff', fontSize: 18, fontFamily: font, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' } },
            labels: { text: { fontSize: 14, fontWeight: 'bold', fill: '#fff', fontFamily: font } },
        },
        colors: overlay.colors || { scheme: personality.scheme },
        margin: { top: 40, right: 40, bottom: 60, left: 80 },
        animate: false,
    };
};
