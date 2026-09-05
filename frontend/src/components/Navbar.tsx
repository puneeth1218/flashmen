import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  ShieldAlert, 
  Activity, 
  BookOpen, 
  X, 
  CheckCircle2, 
  Search, 
  Loader2, 
  Wallet, 
  Network, 
  ArrowRight
} from 'lucide-react';
import { apiClient, globalSearch, SearchResultItem } from '../services/api';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showDocs, setShowDocs] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Poll backend engine health status every 30 seconds
  const { data: healthData, isError: isHealthError } = useQuery({
    queryKey: ['engineHealth'],
    queryFn: async () => {
      const res = await apiClient.get<{ status: string }>('/');
      return res.data;
    },
    refetchInterval: 30000,
    retry: 1,
  });

  const isEngineHealthy = !isHealthError && healthData?.status === 'healthy';

  // Global keyboard shortcut: CMD+K or '/' to focus search bar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === '/' && document.activeElement !== searchInputRef.current) {
        if (!['INPUT', 'TEXTAREA'].includes((document.activeElement as HTMLElement)?.tagName)) {
          e.preventDefault();
          searchInputRef.current?.focus();
        }
      } else if (e.key === 'Escape') {
        setIsDropdownOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Dismiss dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search querying
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await globalSearch(searchQuery.trim());
        setSearchResults(res.results || []);
        setIsDropdownOpen(true);
      } catch (err) {
        console.error('Search failed:', err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectResult = (result: SearchResultItem) => {
    setIsDropdownOpen(false);
    setSearchQuery('');
    navigate(`/graph?entity_id=${encodeURIComponent(result.entity_id)}`);
  };

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <>
      <header className="h-[70px] px-4 md:px-8 flex items-center justify-between bg-zinc-950/85 backdrop-blur-md border-b border-zinc-800/80 sticky top-0 z-40 transition-colors gap-4">
        {/* Left: Brand Identity & Live Beacon */}
        <div className="flex items-center space-x-4 shrink-0">
          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 via-blue-600/20 to-purple-600/20 border border-cyan-500/30 flex items-center justify-center shadow-cyber-glow group-hover:border-cyan-400/60 transition-all">
              <ShieldAlert className="w-4 h-4 text-cyan-400 group-hover:scale-105 transition-transform" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-white font-mono font-bold text-[15px] tracking-wider">
                  Flashmen
                </span>
              </div>
            </div>
          </Link>

          {/* Real-time Core Engine Health Indicator */}
          {isEngineHealthy ? (
            <div className="hidden 2xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/40 text-[11px] font-mono text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-medium tracking-wide">Core Engine Active</span>
            </div>
          ) : (
            <div className="hidden 2xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-950/40 border border-red-800/40 text-[11px] font-mono text-red-400">
              <span className="relative flex h-2 w-2">
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
              </span>
              <span className="font-medium tracking-wide">Engine Disconnected</span>
            </div>
          )}
        </div>

        {/* Center: Main Navigation Tabs */}
        <nav className="hidden lg:flex items-center space-x-1 bg-zinc-900/60 p-1 rounded-xl border border-zinc-800/80 text-[13px] font-medium shrink-0">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-lg transition-all ${
              isActive('/')
                ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700/60'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
            }`}
          >
            Dashboard
          </Link>

          <Link
            to="/graph"
            className={`px-3 py-1.5 rounded-lg transition-all ${
              isActive('/graph')
                ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700/60'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
            }`}
          >
            Graph Explorer
          </Link>
        </nav>

        {/* Right Section: Global Search Bar + Mode Toggle + Docs */}
        <div className="flex items-center space-x-3 shrink-0">
          {/* Global Search Bar */}
          <div className="relative" ref={searchContainerRef}>
            <div className="flex items-center bg-zinc-900/90 border border-zinc-800 rounded-lg px-2.5 py-1.5 focus-within:border-cyan-500/60 focus-within:ring-1 focus-within:ring-cyan-500/30 transition-all w-48 sm:w-60 md:w-72">
              <Search className="w-3.5 h-3.5 text-zinc-400 shrink-0 mr-2" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsDropdownOpen(true)}
                placeholder="Search address, IP, or TxID..."
                className="bg-transparent border-none text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none w-full font-mono"
              />
              {isSearching ? (
                <Loader2 className="w-3 h-3 text-cyan-400 animate-spin shrink-0" />
              ) : searchQuery ? (
                <button
                  type="button"
                  onClick={() => { setSearchQuery(''); setSearchResults([]); setIsDropdownOpen(false); }}
                  className="text-zinc-500 hover:text-zinc-300 p-0.5 shrink-0"
                >
                  <X className="w-3 h-3" />
                </button>
              ) : (
                <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[9px] font-mono font-medium text-zinc-500 bg-zinc-800/80 border border-zinc-700/60 rounded shrink-0">
                  ⌘K
                </kbd>
              )}
            </div>

            {/* Global Search Results Dropdown */}
            {isDropdownOpen && searchQuery.trim().length >= 2 && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-zinc-950/95 border border-zinc-800 rounded-xl shadow-2xl p-2 z-50 backdrop-blur-md max-h-96 overflow-y-auto">
                <div className="px-2 py-1.5 text-[10px] font-mono uppercase tracking-wider text-zinc-500 border-b border-zinc-800/80 flex items-center justify-between">
                  <span>Search Matches</span>
                  <span>{searchResults.length} found</span>
                </div>

                {isSearching ? (
                  <div className="p-4 text-center text-xs text-zinc-400 font-mono flex items-center justify-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                    Searching telemetry database...
                  </div>
                ) : searchResults.length === 0 ? (
                  <div className="p-4 text-center text-xs text-zinc-500 font-mono">
                    No matching alerts or transaction records found.
                  </div>
                ) : (
                  <div className="py-1 space-y-1">
                    {searchResults.map((item, idx) => (
                      <button
                        key={`${item.entity_id}-${idx}`}
                        type="button"
                        onClick={() => handleSelectResult(item)}
                        className="w-full text-left p-2.5 rounded-lg hover:bg-zinc-900/80 border border-transparent hover:border-zinc-800 transition-all group flex flex-col gap-1 cursor-pointer"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-1.5 min-w-0">
                            {item.entity_type === 'wallet' ? (
                              <Wallet className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                            ) : item.entity_type === 'ip' ? (
                              <Network className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                            ) : (
                              <Activity className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                            )}
                            <span className="font-mono text-xs text-zinc-200 truncate group-hover:text-cyan-300 font-medium">
                              {item.entity_id}
                            </span>
                          </div>

                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 ${
                            item.risk_score >= 75
                              ? 'bg-red-950/60 text-red-400 border border-red-800/60'
                              : item.risk_score >= 30
                              ? 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
                              : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                          }`}>
                            {item.risk_score > 0 ? `${item.risk_score.toFixed(0)} Risk` : 'Benign'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[11px] text-zinc-400">
                          <p className="truncate text-zinc-400 text-[11px] leading-snug pr-2">
                            {item.summary}
                          </p>
                          <span className="shrink-0 text-cyan-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5 text-[10px] font-mono">
                            Graph <ArrowRight className="w-3 h-3" />
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
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

