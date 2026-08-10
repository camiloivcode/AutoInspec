import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { ToastProvider } from './context/ToastContext'
// Latin-only subsets: Spanish UI has no use for the cyrillic/vietnamese ranges.
import '@fontsource/overpass/latin-400.css'
import '@fontsource/overpass/latin-600.css'
import '@fontsource/overpass/latin-700.css'
import '@fontsource/overpass-mono/latin-400.css'
import '@fontsource/overpass-mono/latin-700.css'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      gcTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ToastProvider>
          <App />
        </ToastProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
