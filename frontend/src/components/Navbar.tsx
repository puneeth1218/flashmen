import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShieldAlert, Activity, BookOpen, X, Radio, CheckCircle2 } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [networkMode, setNetworkMode] = useState<'live' | 'replay'>('live');
  const [showDocs, setShowDocs] = useState(false);

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <>
      <header className="h-[70px] px-6 md:px-10 flex items-center justify-between bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/80 sticky top-0 z-40 transition-colors">
        {/* Left: Brand Identity & Live Beacon */}
        <div className="flex items-center space-x-6">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500/20 via-blue-600/20 to-purple-600/20 border border-cyan-500/30 flex items-center justify-center shadow-cyber-glow group-hover:border-cyan-400/60 transition-all">
              <ShieldAlert className="w-5 h-5 text-cyan-400 group-hover:scale-105 transition-transform" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-white font-mono font-bold text-[16px] tracking-wider">
                  BTM <span className="text-cyan-400">//</span> SENTINEL
                </span>
                <span className="hidden lg:inline-block px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
                  v2.4
                </span>
              </div>
              <span className="text-[11px] text-zinc-400 tracking-tight hidden sm:inline">
                Bitcoin Traffic & Threat Monitor
              </span>
            </div>
          </Link>

          {/* Pulsing Core Engine Indicator */}
          <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/40 text-[11px] font-mono text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-medium tracking-wide">Core Engine Active</span>
          </div>
        </div>

        {/* Center: Main Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1 bg-zinc-900/60 p-1 rounded-xl border border-zinc-800/80 text-[13px] font-medium">
          <Link
            to="/"
            className={`px-3.5 py-1.5 rounded-lg transition-all ${
              isActive('/')
                ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700/60'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
            }`}
          >
            Dashboard
          </Link>

          <Link
            to="/graph"
            className={`px-3.5 py-1.5 rounded-lg transition-all ${
              isActive('/graph')
                ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700/60'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
            }`}
          >
            Graph Explorer
          </Link>

          <Link
            to="/upload"
            className={`px-3.5 py-1.5 rounded-lg transition-all ${
              isActive('/upload')
                ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700/60'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
            }`}
          >
            Ingestion Pipeline
          </Link>

          <a
            href="#alerts"
            onClick={(e) => {
              if (location.pathname === '/') {
                e.preventDefault();
                document.getElementById('alerts-section')?.scrollIntoView({ behavior: 'smooth' });
              }
            }}
            className="px-3.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 transition-all"
          >
            Alert Center
          </a>
        </nav>

        {/* Right: Network Mode Toggle & Documentation */}
        <div className="flex items-center space-x-3">
          {/* Live / Replay Network Mode Toggle */}
          <div className="flex items-center bg-zinc-900/80 p-1 rounded-lg border border-zinc-800/80 text-[12px] font-mono">
            <button
              type="button"
              onClick={() => setNetworkMode('live')}
              className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all ${
                networkMode === 'live'
                  ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Radio className={`w-3 h-3 ${networkMode === 'live' ? 'text-emerald-400 animate-pulse' : ''}`} />
              Live
            </button>
            <button
              type="button"
              onClick={() => setNetworkMode('replay')}
              className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all ${
                networkMode === 'replay'
                  ? 'bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 font-semibold shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Activity className="w-3 h-3 text-cyan-400" />
              Replay
            </button>
          </div>

          {/* Documentation Trigger Button */}
          <button
            type="button"
            onClick={() => setShowDocs(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800/80 hover:border-zinc-700 text-zinc-300 hover:text-white text-[12px] font-medium transition-all shadow-sm cursor-pointer"
          >
            <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Docs</span>
          </button>
        </div>
      </header>

      {/* Interactive Documentation Modal */}
      {showDocs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl p-6 md:p-8 space-y-6 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/50 flex items-center justify-center text-cyan-400">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white tracking-tight">BTM // Sentinel Documentation</h3>
                  <p className="text-xs text-zinc-400 font-mono">Forensic Bitcoin Traffic Intelligence Architecture</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowDocs(false)}
                className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-sm text-zinc-300 leading-relaxed">
              <div>
                <h4 className="font-semibold text-white mb-1 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                  1. Real-Time Dynamic Anomaly Detection
                </h4>
                <p className="text-zinc-400 text-xs pl-6">
                  Uses an ensemble of Isolation Forest and graph topology heuristics to flag suspicious wallet clustering, peel-chains, and multi-IP Sybil broadcast floods.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-1 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                  2. SHAP Explainability & Risk Attribution
                </h4>
                <p className="text-zinc-400 text-xs pl-6">
                  Every flagged entity receives explainable feature weights quantifying the exact contribution percentage of metrics (e.g. Rapid Multi-IP Broadcast, Volume Surges, High Fan-In/Out).
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-1 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                  3. Telemetry Ingestion Pipeline
                </h4>
                <p className="text-zinc-400 text-xs pl-6">
                  Upload CSV, JSON, or JSONL telemetry captures. The backend parses transaction and P2P layers, updates the topology database, and streams real-time threat scores to the dashboard.
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-zinc-800 flex justify-end">
              <button
                type="button"
                onClick={() => setShowDocs(false)}
                className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-semibold transition-colors cursor-pointer"
              >
                Close Documentation
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

