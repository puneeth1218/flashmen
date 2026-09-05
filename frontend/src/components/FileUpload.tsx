import React, { useRef, useState, DragEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadTrafficFile } from '../services/api/ingest';
import { 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  X, 
  ArrowRight, 
  Sparkles,
  Database
} from 'lucide-react';

export const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: uploadTrafficFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
  });

  const validateAndSetFile = (selectedFile: File) => {
    setLocalError(null);
    const validTypes = ['text/csv', 'application/json', 'application/json-lines'];
    const validExtensions = ['.csv', '.json', '.jsonl'];
    
    const isValidType = validTypes.includes(selectedFile.type) || 
      validExtensions.some(ext => selectedFile.name.toLowerCase().endsWith(ext));

    if (!isValidType) {
      setLocalError('Unsupported file format. Please select a valid .CSV, .JSON, or .JSONL telemetry log.');
      return;
    }
    setFile(selectedFile);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = () => {
    if (file) {
      mutation.mutate(file);
    }
  };

  const clearSelectedFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full bg-gradient-to-b from-zinc-900/90 via-zinc-950/90 to-zinc-950 p-6 md:p-8 rounded-3xl border border-zinc-800/80 shadow-2xl relative overflow-hidden backdrop-blur-md">
      {/* Decorative Cyber Background Elements */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl pointer-events-none -ml-20 -mb-20"></div>

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-zinc-800/80 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              <Database className="w-5 h-5 text-cyan-400" />
              Telemetry Ingestion Pipeline
            </h3>
          </div>
          <p className="text-xs text-zinc-400">
            Feed raw Bitcoin peer-to-peer traffic logs or transaction telemetry into the detection engine.
          </p>
        </div>

        {/* Format Chips */}
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-medium bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
            .CSV
          </span>
          <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-medium bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
            .JSON
          </span>
          <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-medium bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            .JSONL
          </span>
        </div>
      </div>

      {/* Drag & Drop Target */}
      <div className="pt-6 relative z-10">
        <div 
          className={`rounded-2xl p-8 md:p-12 text-center transition-all cursor-pointer border-2 border-dashed relative overflow-hidden ${
            isDragging 
              ? 'border-cyan-400 bg-cyan-950/20 shadow-cyber-glow' 
              : file
                ? 'border-zinc-700 bg-zinc-900/40 hover:border-zinc-600'
                : 'border-zinc-800/90 hover:border-cyan-500/50 bg-zinc-950/40 hover:bg-zinc-900/20'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            accept=".csv,.json,.jsonl"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
          />

          {file ? (
            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 shadow-cyber-glow">
                <FileText className="w-7 h-7" />
              </div>
              <div className="text-center">
                <p className="text-base font-semibold text-white font-mono">{file.name}</p>
                <p className="text-xs text-zinc-400 font-mono mt-0.5">
                  {(file.size / 1024).toFixed(1)} KB · Ready to ingest
                </p>
              </div>
              <button
                type="button"
                onClick={clearSelectedFile}
                className="mt-2 text-xs text-zinc-400 hover:text-red-400 flex items-center gap-1 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 hover:border-red-500/40 transition-colors cursor-pointer"
              >
                <X className="w-3.5 h-3.5" /> Remove file
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-center text-zinc-400 group-hover:text-cyan-400 transition-colors">
                <UploadCloud className="w-7 h-7" />
              </div>
              <div>
                <p className="text-base font-medium text-zinc-200">
                  Select raw Bitcoin telemetry file or drag & drop here
                </p>
                <p className="text-xs text-zinc-400 mt-1">
                  Supported formats: CSV, JSON array, or newline-delimited JSONL
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Upload Progress Bar (during ingestion) */}
        {mutation.isPending && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-cyan-400 font-mono">
              <span className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                Extracting Graph Features & Running Dynamic Scoring...
              </span>
              <span>Processing</span>
            </div>
            <div className="w-full h-2 rounded-full bg-zinc-900 overflow-hidden border border-zinc-800">
              <div className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 animate-pulse rounded-full w-full"></div>
            </div>
          </div>
        )}

        {/* Actions Bar */}
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs text-zinc-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            Ingestion engine ready · Real-time pipeline active
          </div>

          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || mutation.isPending}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-[13px] font-semibold tracking-wide shadow-cyber-glow disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none transition-all cursor-pointer"
          >
            {mutation.isPending ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin" />
                Processing Ingestion...
              </>
            ) : (
              <>
                Ingest & Analyze Telemetry
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Inline Error Notification */}
        {(localError || mutation.isError) && (
          <div className="mt-5 p-4 bg-red-950/30 border border-red-900/60 rounded-xl text-xs text-red-400 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
            <div>
              <p className="font-semibold">Ingestion Error</p>
              <p className="text-red-400/80 mt-0.5">
                {localError || (mutation.error as any)?.response?.data?.detail || 'Failed to ingest file. Verify API connectivity.'}
              </p>
            </div>
          </div>
        )}

        {/* Inline Success Alert Banner */}
        {mutation.isSuccess && mutation.data && (
          <div className="mt-5 p-4 bg-emerald-950/30 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-start gap-3 shadow-emerald-glow">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-emerald-200">
                Telemetry Log Ingested & Scored Successfully
              </p>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-emerald-400/90">
                <span>File: <strong className="text-white">{mutation.data.filename}</strong></span>
                <span>Records: <strong className="text-white">{mutation.data.processed_records}</strong></span>
                <span>Flagged Entities: <strong className="text-white">{mutation.data.generated_alerts_count}</strong></span>
                <span>Pipeline Status: <strong className="text-emerald-400">Score & Attribution Attached</strong></span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
