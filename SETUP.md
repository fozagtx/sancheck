# seccheck - Complete Setup Guide

## What's Been Built

### 1. Enhanced Landing Page UI ✅

The main landing page (`src/App.tsx`) has been enhanced with:
- **Feature Grid**: 4 feature cards showcasing Codex Plugin, URL Gate, Prompt Injection, and Middleware Contract
- **Docs Link**: Added "Docs" button in the topbar linking to the Fumadocs documentation
- **Get Started Button**: Added "Get Started" button in hero section linking to getting-started docs
- **Footer**: Added footer with Documentation and GitHub links
- **Responsive Design**: All new elements are fully responsive

**To run the landing page:**
```bash
npm install
npm run dev
# Open http://localhost:5173
```

### 2. Fumadocs Documentation Site ✅

A complete Fumadocs documentation site has been created in the `docs/` directory with:

#### Documentation Pages:
- **Overview** (`docs/source/docs/index.mdx`) - Landing page with cards linking to all sections
- **Getting Started** (`docs/source/docs/getting-started.mdx`) - Installation and quick start guide
- **Codex Plugin** (`docs/source/docs/plugin.mdx`) - How the plugin package works
- **URL Gate** (`docs/source/docs/url-gate.mdx`) - Deep dive into URL extraction and validation
- **Middleware Contract** (`docs/source/docs/middleware.mdx`) - The stdin-to-JSON contract
- **Configuration** (`docs/source/docs/configuration.mdx`) - All configuration options
- **CLI Reference** (`docs/source/docs/api/cli.mdx`) - Full CLI command reference
- **Scanner API** (`docs/source/docs/api/scanner.mdx`) - Python API reference
- **Plugin Skills** (`docs/source/docs/api/skills.mdx`) - Plugin skills reference

#### Features:
- Full-text search
- Responsive design
- Dark mode support
- Syntax highlighting
- Navigation sidebar
- Breadcrumbs

**To run the docs:**
```bash
cd docs
npm install
npm run dev
# Open http://localhost:3333/docs
```

**To build the docs:**
```bash
cd docs
npm run build
npm run start
```

### 3. Codex Plugin Package ✅

The plugin package at `plugins/seccheck/` is complete with:
- **Plugin Manifest** (`.codex-plugin/plugin.json`) - Plugin metadata and configuration
- **URL Gate Skill** (`skills/url-gate/SKILL.md`) - Skill instructions for the agent
- **Gate Script** (`scripts/seccheck-gate`) - Entry point shell script
- **Bundled Scanner** (`scripts/src/seccheck/`) - Complete scanner source
- **Assets** (`assets/`) - Logo and favicon

## Project Structure

```
seccheck/
├── src/                          # Main landing page (Vite + React)
│   ├── App.tsx                   # Enhanced landing page with feature grid
│   ├── main.tsx                  # Entry point
│   └── styles.css                # Styles with feature grid and footer
├── docs/                         # Fumadocs documentation site (Next.js)
│   ├── app/                      # Next.js app router
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Home page
│   │   ├── docs/                 # Docs pages
│   │   │   ├── layout.tsx        # Docs layout
│   │   │   └── [...slug]/        # Dynamic docs pages
│   │   ├── api/search/           # Search API
│   │   └── css/                  # Global styles
│   ├── source/                   # MDX content
│   │   └── docs/                 # Documentation pages
│   │       ├── index.mdx
│   │       ├── getting-started.mdx
│   │       ├── plugin.mdx
│   │       ├── url-gate.mdx
│   │       ├── middleware.mdx
│   │       ├── configuration.mdx
│   │       └── api/              # API reference
│   ├── source.ts                 # Source configuration
│   ├── source.config.ts          # MDX configuration
│   ├── next.config.ts            # Next.js configuration
│   └── package.json              # Docs dependencies
├── plugins/seccheck/             # Codex plugin package
│   ├── .codex-plugin/
│   │   └── plugin.json           # Plugin manifest
│   ├── skills/
│   │   └── url-gate/
│   │       └── SKILL.md          # URL gate skill
│   ├── scripts/
│   │   ├── seccheck-gate         # Gate script
│   │   └── src/seccheck/         # Bundled scanner
│   └── assets/                   # Plugin assets
├── src/seccheck/                 # Python scanner source
│   ├── scanner.py                # Main scanner
│   ├── cli.py                    # CLI interface
│   ├── models.py                 # Data models
│   └── ...                       # Other modules
└── package.json                  # Main app dependencies
```

## Quick Start

### Run the Landing Page
```bash
npm install
npm run dev
# Open http://localhost:5173
```

### Run the Documentation
```bash
cd docs
npm install
npm run dev
# Open http://localhost:3333/docs
```

### Use the Plugin
```bash
# Scan a URL
PYTHONPATH=src python3 -m seccheck scan https://example.com

# Use the gate
printf 'check https://example.com' | ./scripts/seccheck-gate

# Use the plugin
printf '{"text":"open https://example.com"}' | plugins/seccheck/scripts/seccheck-gate
```

## Build Everything

```bash
# Build the landing page
npm run build

# Build the docs
cd docs && npm run build

# Run tests
npm run check
```

## Notes

- The main landing page builds successfully and is ready to use
- The Fumadocs documentation site structure is complete but may require additional configuration based on the Fumadocs version
- The Codex plugin package is complete and functional
- All Python tests pass
- The scanner uses only the Python standard library (no external dependencies)
