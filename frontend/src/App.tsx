import { C1Chat, ThemeProvider } from '@thesysai/genui-sdk'
import '@crayonai/react-ui/styles/index.css'
import './App.css'

function App() {
  return (
    <main className="app-shell">
      <header className="app-header">
        <a className="brand" href="/" aria-label="EquityLens home">
          <span className="brand-mark" aria-hidden="true">E</span>
          <span>EquityLens</span>
        </a>
        <span className="header-context">AI STOCK RESEARCH / MARKET DATA TOOLS</span>
        <span className="status-indicator"><span /> Research assistant</span>
      </header>
      <section className="chat-stage" aria-label="EquityLens stock research assistant">
        <ThemeProvider mode="dark">
          <C1Chat apiUrl="/api/chat" />
        </ThemeProvider>
      </section>
      <footer className="app-footer">
        <span>Yahoo Finance data may be delayed or incomplete.</span>
        <span>Educational research only. Not investment advice.</span>
      </footer>
    </main>
  )
}

export default App