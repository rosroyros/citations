# Nginx Configuration for Citations Platform

## Overview

This nginx configuration serves multiple components:
- React SPA (main application) at `/`
- PSEO mega guides at `/guide/`
- PSEO source type guides at `/how-to-cite-*-apa/`
- Static assets for guides at `/assets/`
- Backend API at `/api/`

## Critical Points

### Location Block Ordering

**ORDER MATTERS!** Nginx processes location blocks in a specific order:

1. `/assets/` - MUST come first to serve PSEO guide CSS/JS
2. `/how-to-cite-*-apa/` - Source type guides (27 guides)
3. `/guide/` - Mega guides (15 guides)
4. `/` - React app (MUST be last to avoid overriding other routes)

If `/` comes before `/assets/`, the React app will serve HTML instead of CSS files, causing MIME type errors.

### Directory Structure

```
/opt/citations/
├── frontend/frontend/dist/     # React app build
│   ├── index.html
│   ├── assets/                 # React app assets (NOT PSEO)
│   └── ...
└── content/dist/               # PSEO guides
    ├── assets/                 # PSEO guide assets (CSS/JS)
    │   ├── css/
    │   │   ├── styles.css
    │   │   └── mini-checker.css
    │   └── js/
    ├── how-to-cite-*-apa/     # 27 source type guides
    ├── guide/                  # 15 mega guides
    └── sitemap.xml
```

### Asset Serving

Two separate `/assets/` directories:
- `/opt/citations/content/dist/assets/` → Serves PSEO guide CSS/JS at `/assets/`
- `/opt/citations/frontend/frontend/dist/assets/` → Bundled in React app, served via `/` route

### Alias vs Root

- **`alias`**: Used for regex locations (`/how-to-cite-*-apa/`) - replaces matched portion
- **`root`**: Used for simple prefix locations (`/guide/`, `/assets/`) - appends path

## Deployment

After updating this config:

```bash
# Copy to production
scp deployment/nginx/citations.conf deploy@178.156.161.140:/tmp/

# SSH to server
ssh deploy@178.156.161.140

# Test config
sudo cp /tmp/citations.conf /etc/nginx/sites-available/
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Common Issues

### CSS Not Loading (MIME Type Error)

**Symptom**: Console error "Did not parse stylesheet because non CSS MIME types are not allowed"

**Cause**: `/` location block serving HTML instead of CSS files

**Fix**: Ensure `/assets/` location comes before `/` location

### 500 Internal Server Error (Redirect Cycle)

**Symptom**: Nginx log shows "rewrite or internal redirection cycle"

**Cause**: Using `root` with regex location instead of `alias`

**Fix**: Use `alias` for regex locations like `/how-to-cite-*-apa/`

### React App Routes Return 404

**Symptom**: Direct navigation to React routes fails

**Cause**: `try_files` not falling back to `index.html`

**Fix**: Ensure `/` location has `try_files $uri $uri/ /index.html;`
