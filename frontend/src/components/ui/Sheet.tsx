import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export interface SheetProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}

export const Sheet: React.FC<SheetProps> = ({ isOpen, onClose, children, title }) => {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleEsc);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleEsc);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end animate-in fade-in duration-200">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Sheet Content Drawer */}
      <div className="relative w-full max-w-lg h-full bg-zinc-950 border-l border-zinc-800/90 shadow-2xl flex flex-col z-10 animate-in slide-in-from-right duration-300 ease-out">
        <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-800/80 bg-zinc-950/60 backdrop-blur-md">
          <div className="flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
            <h2 className="text-base font-bold text-white tracking-tight font-mono">
              {title || 'Entity Inspection'}
            </h2>
          </div>
          <button 
            type="button"
            onClick={(e) => { e.stopPropagation(); onClose(); }}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-600 cursor-pointer"
            aria-label="Close drawer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          {children}
        </div>
      </div>
    </div>
  );
};
