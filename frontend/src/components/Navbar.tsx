import React from 'react';
import { Link } from 'react-router-dom';

export const Navbar: React.FC = () => {
  return (
    <nav className="h-[60px] px-6 md:px-12 flex items-center bg-transparent sticky top-0 z-50">
      <div className="flex items-center space-x-3 mr-10">
        <div className="w-6 h-6 bg-white rounded-md flex items-center justify-center">
          <span className="text-black font-bold text-[14px]">A</span>
        </div>
        <Link to="/" className="text-white font-bold text-[18px] tracking-tight">
          Aceternity
        </Link>
      </div>

      <div className="hidden md:flex items-center space-x-8 text-[14px] font-medium text-mid-gray">
        <Link to="/" className="hover:text-white transition-colors">
          Dashboard
        </Link>

        <Link to="/graph" className="hover:text-white transition-colors">
          Graph Explorer
        </Link>

        <Link to="/upload" className="hover:text-white transition-colors">
          Ingest Logs
        </Link>
      </div>
    </nav>
  );
};

