import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Users, Play, PlusCircle, Activity, GitCompare } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  return (
    <header className="top-nav">
      <div className="brand">
        <Users size={22} color="#3b82f6" />
        <Link to="/experiments" style={{ color: 'inherit', textDecoration: 'none' }}>
          Synthetic Humans
        </Link>
        <span className="brand-badge">HCI Simulation Platform</span>
      </div>

      <nav className="nav-links">
        <Link
          to="/experiments"
          className={`nav-link ${location.pathname === '/experiments' ? 'active' : ''}`}
        >
          <Activity size={16} />
          Experiments
        </Link>
        <Link
          to="/experiments/new"
          className={`nav-link ${location.pathname === '/experiments/new' ? 'active' : ''}`}
        >
          <PlusCircle size={16} />
          New Simulation
        </Link>
      </nav>
    </header>
  );
};
