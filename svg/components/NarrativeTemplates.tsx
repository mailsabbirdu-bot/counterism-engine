import React, { useMemo } from 'react';
import { COMPOSITIONS, CompositionDefinition } from '../lib/compositionLibrary';
import { HubNetwork } from './HubNetwork';
import { FlowDiagram } from './FlowDiagram';
import { ProcessDiagram } from './ProcessDiagram';
import { LabelSystem } from './LabelSystem';
import { CalloutSystem } from './CalloutSystem';
import { KpiCard } from './KpiCard';
import { Timeline } from './Timeline';
import { HubNetworkElement, FlowDiagramElement, ProcessElement, LabelElement, CalloutElement, KpiElement, TimelineElement, StorytellingElement, SvgProvider } from '../types';

/**
 * Narrative Template Engine
 * Automatically expands high-level story templates into visual components.
 */
export const expandNarrativeTemplate = (storyType: string, startFrame: number = 0): StorytellingElement[] => {
    switch (storyType) {
        case 'hub_explanation':
            return [
                {
                    id: 'story_hub',
                    type: 'hub_network',
                    centerSvg: 'network',
                    nodes: ['database', 'cpu', 'cloud', 'lock'],
                    radius: 300,
                    x: 960,
                    y: 540,
                    startFrame
                } as HubNetworkElement,
                {
                    id: 'hub_label',
                    type: 'label',
                    target: 'story_hub_center',
                    text: 'Central Intelligence',
                    position: 'top',
                    startFrame: startFrame + 30
                } as LabelElement
            ];
        case 'process_breakdown':
            return [
                {
                    id: 'story_process',
                    type: 'process',
                    steps: ['search', 'settings', 'code-2', 'rocket'],
                    x: 960,
                    y: 540,
                    startFrame
                } as ProcessElement
            ];
        case 'timeline_story':
            return [
                {
                    id: 'story_timeline',
                    type: 'timeline',
                    events: [
                        { year: '2020', label: 'Inception' },
                        { year: '2022', label: 'Growth' },
                        { year: '2024', label: 'Scale' }
                    ],
                    x: 960,
                    y: 540,
                    startFrame
                } as TimelineElement
            ];
        default:
            return [];
    }
};

interface TemplateProps {
    story?: string;
    startFrame?: number;
    sceneIconTheme?: SvgProvider;
    positionMap: Record<string, { x: number, y: number }>;
}

/**
 * Narrative Template Component
 * HARDENING: Correctly renders all expanded elements (P2-4).
 */
export const NarrativeTemplate: React.FC<TemplateProps> = ({ story, startFrame = 0, sceneIconTheme, positionMap }) => {
    const elements = useMemo(() => story ? expandNarrativeTemplate(story, startFrame) : [], [story, startFrame]);
    if (!elements.length) return null;

    return (
        <>
            {elements.map((el: any) => {
                switch(el.type) {
                    case 'hub_network': return <HubNetwork key={el.id} element={el} sceneIconTheme={sceneIconTheme} />;
                    case 'process': return <ProcessDiagram key={el.id} element={el} sceneIconTheme={sceneIconTheme} />;
                    case 'timeline': return <Timeline key={el.id} element={el} />;
                    case 'label': return <LabelSystem key={el.id} element={el} targetPos={positionMap[el.target]} />;
                    case 'callout': return <CalloutSystem key={el.id} element={el} targetPos={positionMap[el.target]} />;
                    default: return null;
                }
            })}
        </>
    );
};
