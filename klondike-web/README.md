# Klondike Web UI

React SPA for the Klondike Spec CLI project management interface.

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS v4** for styling
- **React Router** for client-side routing
- **HeroIcons** for UI icons

## Development

```bash
cd klondike-web
npm install
npm run dev
```

The dev server will start at http://localhost:5173

## Building

```bash
npm run build
```

This builds the production bundle and outputs to `../src/klondike_spec_cli/static/` for packaging with the Python CLI.

## Project Structure

```
src/
├── components/
│   ├── Layout.tsx         # Main layout with sidebar navigation
│   ├── Dashboard.tsx      # Project overview dashboard
│   ├── SpecExplorer.tsx   # Feature list and filtering
│   ├── ActivityLog.tsx    # Session history
│   └── ConfigEditor.tsx   # Project configuration
├── hooks/
│   └── useWebSocket.ts    # WebSocket hook for real-time updates
├── App.tsx                # Main app with routing
└── main.tsx               # Entry point
```

## Features

- ✅ React + TypeScript + Vite setup
- ✅ Tailwind CSS v4 styling
- ✅ React Router for navigation
- ✅ WebSocket hook for real-time updates
- ✅ Build output to Python package
- ✅ Component scaffolding for all main views

## Integration with Python Package

The Vite build is configured to output to `../src/klondike_spec_cli/static/`, which is included in the Python package. The FastAPI server in the CLI serves these static files with proper fallback to `index.html` for client-side routing.

## Next Steps

- Implement API endpoints in FastAPI backend
- Connect components to REST API
- Add WebSocket support in FastAPI for real-time updates
- Implement feature CRUD operations
- Add session management UI
- Build data visualization components
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
