import React, { useState } from 'react';
import { uploadTrafficFile, IngestResponse } from '../services/api';
import { CheckCircle, AlertCircle, FileText } from 'lucide-react';

export const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV or JSON file to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const response = await uploadTrafficFile(file);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process file ingestion.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-[800px] mx-auto mt-20 relative z-10">
      <div className="mb-10">
        <h1 className="text-[40px] font-bold tracking-apple-heading text-white flex items-center gap-3">
          Ingest Telemetry
        </h1>
        <p className="text-[14px] tracking-apple-body text-mid-gray mt-2">
          Upload raw CSV or JSON Bitcoin network PCAP logs for ingestion, parsing, and anomaly scoring.
        </p>
      </div>

      <form onSubmit={handleUpload} className="bg-paper rounded-apple-card border border-hairline p-10 space-y-8">
        <div 
          className={`rounded-apple-card p-12 text-center transition-colors cursor-pointer border ${
            file ? 'border-white bg-white/5' : 'border-hairline hover:border-mid-gray bg-transparent'
          }`}
          onClick={() => document.getElementById('file-upload')?.click()}
        >
          <FileText className="h-12 w-12 text-mid-gray mx-auto mb-4" strokeWidth={1.5} />
          <input
            type="file"
            accept=".csv,.json,.jsonl"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          
          {file ? (
            <div className="text-[14px] tracking-apple-body text-white">
              <span className="font-semibold">{file.name}</span>
              <span className="text-mid-gray ml-2">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          ) : (
            <div>
              <p className="text-white text-[14px] font-medium tracking-apple-body">Click to browse or drop file here</p>
              <p className="text-mid-gray text-[12px] tracking-apple-body mt-1">Supports .CSV, .JSON, .JSONL files</p>
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 bg-red-950/30 border border-ember/30 rounded-lg text-ember text-[14px] tracking-apple-body flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="p-4 bg-green-950/30 border border-green-500/30 rounded-lg text-green-500 text-[14px] tracking-apple-body flex items-start gap-3">
            <CheckCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">{result.message}</p>
              <ul className="text-[12px] text-green-500/80 mt-1 space-y-1">
                <li>• Processed Records: {result.processed_records}</li>
                <li>• Flagged Suspicious Entities: {result.generated_alerts_count}</li>
              </ul>
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!file || uploading}
            className="flex items-center gap-2 px-8 py-3 bg-white text-black text-[14px] font-bold tracking-apple-body rounded-apple-pill hover:opacity-90 disabled:bg-cool-wash disabled:text-mid-gray disabled:cursor-not-allowed transition-all"
          >
            {uploading ? 'Processing & Scoring...' : 'Ingest & Run Models'}
          </button>
        </div>
      </form>
    </div>
  );
};
