import React, { createContext, useContext, useState, useCallback } from 'react';

export interface FocalTarget {
    id: string;
    x: number;
    y: number;
    zoom?: number;
    importance: number;
    weight: number;
    category?: string;
}

interface FocusContextType {
    targets: Record<string, FocalTarget>;
    registerTarget: (target: FocalTarget) => void;
    unregisterTarget: (id: string) => void;
}

const FocusContext = createContext<FocusContextType | undefined>(undefined);

export const FocusProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [targets, setTargets] = useState<Record<string, FocalTarget>>({});

    const registerTarget = useCallback((target: FocalTarget) => {
        setTargets(prev => ({ ...prev, [target.id]: target }));
    }, []);

    const unregisterTarget = useCallback((id: string) => {
        setTargets(prev => {
            const next = { ...prev };
            delete next[id];
            return next;
        });
    }, []);

    return (
        <FocusContext.Provider value={{ targets, registerTarget, unregisterTarget }}>
            {children}
        </FocusContext.Provider>
    );
};

export const useFocus = () => {
    const context = useContext(FocusContext);
    if (!context) {
        throw new Error('useFocus must be used within a FocusProvider');
    }
    return context;
};
