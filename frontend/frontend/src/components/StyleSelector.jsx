import { useState, useEffect } from 'react';
import { trackEvent } from '../utils/analytics';
import './StyleSelector.css';

/**
 * StyleSelector - Tab-based UI for selecting citation styles (APA 7 / MLA 9)
 * 
 * @param {Object} props
 * @param {string} props.selectedStyle - Currently selected style ('apa7' or 'mla9')
 * @param {function} props.onStyleChange - Callback when style changes
 * @param {boolean} props.disabled - Whether the selector should be disabled
 */
export const StyleSelector = ({ selectedStyle, onStyleChange, disabled = false }) => {
    const [availableStyles, setAvailableStyles] = useState({ apa7: 'APA 7th Edition' });
    const [loading, setLoading] = useState(true);

    // Fetch available styles from backend on mount
    useEffect(() => {
        const fetchStyles = async () => {
            try {
                const response = await fetch('/api/styles');
                if (response.ok) {
                    const data = await response.json();
                    setAvailableStyles(data.styles);
                }
            } catch (error) {
                console.error('Failed to fetch styles:', error);
                // Fallback to APA only
            } finally {
                setLoading(false);
            }
        };

        fetchStyles();
    }, []);

    // Handle URL param for style pre-selection (for PSEO pages)
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const styleParam = urlParams.get('style');
        if (styleParam && availableStyles[styleParam]) {
            onStyleChange(styleParam);
        }
    }, [availableStyles, onStyleChange]);

    const handleStyleClick = (styleKey) => {
        if (disabled || styleKey === selectedStyle) return;

        // Track style change event
        trackEvent('style_changed', {
            from_style: selectedStyle,
            to_style: styleKey,
            interface_source: 'style_selector'
        });

        onStyleChange(styleKey);
    };

    // Don't show selector if only one style available
    const styleKeys = Object.keys(availableStyles);
    if (loading || styleKeys.length <= 1) {
        return null;
    }

    return (
        <div className="style-selector" role="tablist" aria-label="Citation style selector">
            {styleKeys.map((styleKey) => (
                <button
                    key={styleKey}
                    role="tab"
                    aria-selected={selectedStyle === styleKey}
                    aria-controls="citation-editor"
                    className={`style-tab ${selectedStyle === styleKey ? 'style-tab--active' : ''}`}
                    onClick={() => handleStyleClick(styleKey)}
                    disabled={disabled}
                >
                    {availableStyles[styleKey]}
                </button>
            ))}
        </div>
    );
};

export default StyleSelector;
