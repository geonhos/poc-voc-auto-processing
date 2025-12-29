/**
 * Main App Component with Routing
 */

import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { TicketListPage } from './pages/TicketListPage';
import { VocInputPage } from './pages/VocInputPage';
import { TicketDetailPage } from './pages/TicketDetailPage';
import './App.css';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <div className="app-header-content">
            <Link to="/" className="app-logo">
              VOC Auto Processing
            </Link>
            <nav className="app-nav">
              <Link to="/">Tickets</Link>
              <Link to="/voc/new">New VOC</Link>
            </nav>
          </div>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<TicketListPage />} />
            <Route path="/voc/new" element={<VocInputPage />} />
            <Route path="/tickets/:id" element={<TicketDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
