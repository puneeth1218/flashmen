import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, ShieldAlert, UploadCloud, GitFork, Search } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/graph?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
      <div className="flex items-center space-x-3">
        <Activity className="h-7 w-7 text-amber-500" />
        <Link to="/" className="text-xl font-bold text-white tracking-wide">
          Bitcoin Traffic Monitor
        </Link>
      </div>

      <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search IP, Wallet address, or TxID..."
          className="w-full bg-gray-900 text-gray-200 pl-10 pr-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:border-amber-500 text-sm"
        />
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
      </form>

      <div className="flex items-center space-x-6">
        <Link
          to="/"
          className="flex items-center space-x-2 text-gray-300 hover:text-amber-500 font-medium text-sm transition"
        >
          <ShieldAlert className="h-4 w-4" />
          <span>Dashboard</span>
        </Link>

        <Link
          to="/graph"
          className="flex items-center space-x-2 text-gray-300 hover:text-amber-500 font-medium text-sm transition"
        >
          <GitFork className="h-4 w-4" />
          <span>Graph Explorer</span>
        </Link>

        <Link
          to="/upload"
          className="flex items-center space-x-2 bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition"
        >
          <UploadCloud className="h-4 w-4" />
          <span>Ingest Logs</span>
        </Link>
      </div>
    </nav>
  );
};
