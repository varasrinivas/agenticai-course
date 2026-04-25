# Visual Design System

## Color Palette

```css
:root {
  /* Primary */
  --bg-primary: #0A1628;
  --bg-secondary: #111D33;
  --bg-card: #162033;
  --bg-surface: #1A2740;
  
  /* Text */
  --text-primary: #E8ECF1;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  
  /* Accent */
  --accent-primary: #D4A843;
  --accent-hover: #E5BC5A;
  --accent-muted: rgba(212, 168, 67, 0.15);
  
  /* Semantic */
  --success: #10B981;
  --success-bg: rgba(16, 185, 129, 0.1);
  --warning: #F59E0B;
  --warning-bg: rgba(245, 158, 11, 0.1);
  --error: #F43F5E;
  --error-bg: rgba(244, 63, 94, 0.1);
  --info: #3B82F6;
  --info-bg: rgba(59, 130, 246, 0.1);
  
  /* Track Signature Colors */
  --track-foundations: #6366F1;    /* Indigo */
  --track-tooluse: #8B5CF6;       /* Violet */
  --track-memory: #06B6D4;        /* Cyan */
  --track-architecture: #F97316;  /* Orange */
  --track-guardrails: #EF4444;    /* Red */
  --track-observability: #22C55E; /* Green */
  --track-deployment: #3B82F6;    /* Blue */
  --track-capstones: #D4A843;     /* Gold */
  
  /* Code Editor */
  --code-bg: #0D1117;
  --code-border: #21262D;
  --code-text: #C9D1D9;
  --code-comment: #8B949E;
  --code-keyword: #FF7B72;
  --code-string: #A5D6FF;
  --code-function: #D2A8FF;
  --code-number: #79C0FF;
  
  /* Animation */
  --animation-speed: 1;
  --transition-fast: 150ms;
  --transition-normal: 300ms;
  --transition-slow: 500ms;
}
```

## Typography

Import from Google Fonts CDN:
```html
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700;800&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
```

| Role | Font | Weight | Size |
|---|---|---|---|
| Course title | Bricolage Grotesque | 800 | 2.5rem |
| Module title | Bricolage Grotesque | 700 | 2rem |
| Section heading (H2) | Bricolage Grotesque | 700 | 1.5rem |
| Subsection heading (H3) | Bricolage Grotesque | 600 | 1.25rem |
| Body text | Source Sans 3 | 400 | 1.05rem, line-height 1.7 |
| Body emphasis | Source Sans 3 | 600 | 1.05rem |
| Code inline | JetBrains Mono | 400 | 0.9rem |
| Code block | JetBrains Mono | 400 | 0.85rem, line-height 1.6 |
| Tooltip | Source Sans 3 | 400 | 0.85rem |
| Quiz text | Source Sans 3 | 400 | 1rem |
| Navigation | Bricolage Grotesque | 600 | 0.85rem |

## Layout

```css
/* Page structure */
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 3rem;
}

/* Sidebar navigation — sticky */
.sidebar-nav {
  position: sticky;
  top: 2rem;
  height: calc(100vh - 4rem);
  overflow-y: auto;
}

/* Content area */
.content {
  max-width: 800px;
}

/* Section spacing */
.section { margin-bottom: 4rem; }
.subsection { margin-bottom: 2.5rem; }

/* Responsive */
@media (max-width: 900px) {
  .page-container {
    grid-template-columns: 1fr;
  }
  .sidebar-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: auto;
    z-index: 100;
  }
}
```

## Component Styles

### Analogy Box
```css
.analogy-box {
  background: var(--accent-muted);
  border-left: 4px solid var(--accent-primary);
  border-radius: 0 8px 8px 0;
  padding: 1.5rem;
  margin: 1.5rem 0;
}
.analogy-box::before {
  content: '💡 Everyday Analogy';
  font-family: 'Bricolage Grotesque', sans-serif;
  font-weight: 700;
  color: var(--accent-primary);
  display: block;
  margin-bottom: 0.5rem;
}
```

### Technical Definition Box
```css
.tech-def-box {
  background: var(--info-bg);
  border-left: 4px solid var(--info);
  border-radius: 0 8px 8px 0;
  padding: 1.5rem;
  margin: 1.5rem 0;
}
.tech-def-box::before {
  content: '📐 Technical Definition';
  font-family: 'Bricolage Grotesque', sans-serif;
  font-weight: 700;
  color: var(--info);
  display: block;
  margin-bottom: 0.5rem;
}
```

### Warning / Cost / Security Callouts
```css
.callout-warning { background: var(--warning-bg); border-left-color: var(--warning); }
.callout-cost { background: var(--warning-bg); border-left-color: var(--accent-primary); }
.callout-security { background: var(--error-bg); border-left-color: var(--error); }
.callout-why { background: var(--success-bg); border-left-color: var(--success); }
```

### Code Tabs (Python / Node.js)
```css
.code-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--code-border);
}
.code-tab {
  padding: 0.5rem 1.25rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  color: var(--text-muted);
  transition: all var(--transition-fast);
}
.code-tab.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}
```

### Animation Container
```css
.animation-container {
  background: var(--bg-secondary);
  border: 1px solid var(--code-border);
  border-radius: 12px;
  padding: 2rem;
  margin: 2rem 0;
  position: relative;
  min-height: 300px;
}
.animation-controls {
  display: flex;
  gap: 0.5rem;
  position: absolute;
  bottom: 1rem;
  right: 1rem;
}
.animation-controls button {
  background: var(--bg-card);
  border: 1px solid var(--code-border);
  color: var(--text-primary);
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  transition: all var(--transition-fast);
}
.animation-controls button:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}
```

### Quiz Styles
```css
.quiz-question {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.quiz-option {
  padding: 0.75rem 1rem;
  margin: 0.5rem 0;
  border: 1px solid var(--code-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.quiz-option:hover { border-color: var(--accent-primary); }
.quiz-option.correct { border-color: var(--success); background: var(--success-bg); }
.quiz-option.incorrect { border-color: var(--error); background: var(--error-bg); }
.quiz-feedback {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
}
```

### Tooltip (for technical terms)
```css
.term-tooltip {
  position: relative;
  color: var(--accent-primary);
  cursor: help;
  border-bottom: 1px dashed var(--accent-primary);
}
.term-tooltip .tooltip-content {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-card);
  border: 1px solid var(--accent-primary);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  color: var(--text-primary);
  width: 280px;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-fast);
  z-index: 10;
}
.term-tooltip:hover .tooltip-content { opacity: 1; }
```

### Progress Bar
```css
.progress-bar {
  height: 4px;
  background: var(--bg-surface);
  border-radius: 2px;
  overflow: hidden;
  margin: 1rem 0;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--track-color), var(--accent-primary));
  border-radius: 2px;
  transition: width var(--transition-slow);
}
```
