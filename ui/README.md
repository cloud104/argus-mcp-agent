# Argus UI

Angular 18 frontend with NGINX for the Argus SRE Agent.

## Overview

Modern web interface for log analysis and AI-powered SRE assistance:

- **Authentication**: Login/logout with JWT tokens
- **Log Explorer**: Search, filter, and analyze TOTVS Protheus logs
- **Deep Dive Analysis**: AI-powered log synthesis and insights
- **Chat Interface**: Conversational AI for troubleshooting
- **TOTVS Design System**: Custom theming based on TOTVS branding

## Architecture

- **Framework**: Angular 18 (standalone components)
- **UI Components**: Angular Material + Custom TOTVS components
- **Charts**: ng2-charts (Chart.js)
- **Server**: NGINX (multi-stage Docker build)
- **State Management**: Angular signals

## Directory Structure

```
ui/
├── src/
│   ├── app/
│   │   ├── core/           # Auth, guards, interceptors, API service
│   │   ├── features/       # Log Explorer, Login components
│   │   └── shared/         # Reusable components
│   ├── styles/
│   │   ├── _totvs-theme.scss       # TOTVS color palette
│   │   └── _totvs-components.scss  # Reusable UI components
│   └── environments/       # Environment configs
├── nginx.conf              # NGINX reverse proxy config
├── Dockerfile              # Production build (Node + NGINX)
├── Dockerfile.dev          # Development with hot-reload
└── package.json            # Node dependencies
```

## Running Locally

### Development Mode

```bash
# Install dependencies
cd ui
npm install

# Run dev server (http://localhost:4200)
npm start

# Or with Angular CLI
ng serve
```

### Docker Development

```bash
# Build development image
docker build -f ui/Dockerfile.dev -t argus-ui:dev ./ui

# Run with docker-compose
docker-compose -f docker-compose.dev.yml up ui
```

## Building

```bash
# Production build
npm run build

# Build output: dist/ui/browser
```

## TOTVS Design System

### Color Palette

- **Primary Blue**: `#0033A0` - TOTVS brand color
- **Primary Green**: `#00B388` - Success/positive actions
- **Warning Orange**: `#FF8C00` - Warnings and caution
- **Error Red**: `#DC3545` - Errors and critical issues

### Reusable Components

All custom components are defined in `src/styles/_totvs-components.scss`:

- `.totvs-card` - Content cards with elevation
- `.totvs-btn`, `.totvs-btn-primary`, `.totvs-btn-secondary` - Buttons
- `.totvs-input` - Text inputs
- `.totvs-pill-*` - Severity pills (info, success, warning, error)
- `.totvs-spinner` - Loading spinner
- `.totvs-alert-*` - Alert boxes

## Features

### Authentication

- JWT-based authentication with auto-refresh
- Auth guard protecting routes
- HTTP interceptor adding Bearer tokens

### Log Explorer

- Time range selection
- Index dropdown
- Log filtering with removable pills
- Severity highlighting (INFO, WARN, ERROR)
- Insights panel with AI-generated summaries

### API Integration

All API calls are typed via `ApiService`:

```typescript
// Search logs
api.initialAnalysis(params).subscribe(...)

// Deep dive
api.deepDive(logs).subscribe(...)

// Chat
api.chat(message, context).subscribe(...)

// Explain log line
api.explainLogLine(logLine).subscribe(...)
```

## Environment Configuration

### Development (`src/environments/environment.ts`)

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000'
};
```

### Production (`src/environments/environment.prod.ts`)

```typescript
export const environment = {
  production: true,
  apiUrl: ''  // Uses relative paths via NGINX proxy
};
```

## NGINX Configuration

The `nginx.conf` file configures reverse proxy to the API:

- `/api/` → `http://argus-api:8000/api/`
- `/auth/` → `http://argus-api:8000/auth/`
- `/initial-analysis` → `http://argus-api:8000/initial-analysis`
- `/deep-dive` → `http://argus-api:8000/deep-dive`
- `/chat` → `http://argus-api:8000/chat`
- `/explain-log-line` → `http://argus-api:8000/explain-log-line`
- `/health/` → `http://argus-api:8000/health/`

Long timeouts (180s) are configured for AI operations.

## Deployment

### Docker Production

```bash
# Build production image (multi-stage)
docker build -f ui/Dockerfile -t argus-ui:latest ./ui

# Push to registry
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-ui:latest
```

The production image:
1. **Builder stage**: `node:20-alpine` builds Angular app
2. **Runtime stage**: `nginx:alpine` serves static files
3. Final size: ~270KB (gzipped ~75KB)

### Kubernetes

See `/ui/k8s/ui-deployment.yaml` for K8s deployment manifests.

## Testing

```bash
# Unit tests
npm test

# E2E tests
npm run e2e

# Linting
npm run lint
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Angular CLI Commands

This project was generated with [Angular CLI](https://github.com/angular/angular-cli) version 18.2.21.

### Development server
Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.

### Code scaffolding
Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

### Build
Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory.

### Running unit tests
Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

### Running end-to-end tests
Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

### Further help
To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
