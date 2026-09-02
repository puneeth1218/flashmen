import React, { useState } from 'react';
import { uploadTrafficFile, IngestResponse } from '../services/api';
import { UploadCloud, CheckCircle, AlertCircle, FileText } from 'lucide-react';

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
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <UploadCloud className="h-6 w-6 text-amber-500" />
          Ingest Network Traffic Logs
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Upload raw CSV or JSON Bitcoin network PCAP logs for ingestion, parsing, and anomaly scoring.
        </p>
      </div>

      <form onSubmit={handleUpload} className="bg-gray-800 p-8 rounded-xl border border-gray-700 space-y-6">
        <div className="border-2 border-dashed border-gray-600 rounded-xl p-8 text-center hover:border-amber-500 transition">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <input
            type="file"
            accept=".csv,.json,.jsonl"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer font-medium text-amber-400 hover:text-amber-300"
          >
            Click to browse
          </label>
          <span className="text-gray-400 text-sm"> or drop file here</span>
          <p className="text-xs text-gray-500 mt-2">Supports .CSV, .JSON, .JSONL files</p>

          {file && (
            <div className="mt-4 p-3 bg-gray-900 rounded-lg text-sm font-mono text-gray-200 inline-block border border-gray-700">
              Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="p-4 bg-emerald-900/40 border border-emerald-700 rounded-lg text-emerald-300 text-sm flex items-start gap-3">
            <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">{result.message}</p>
              <ul className="text-xs text-emerald-400/90 mt-1 space-y-1">
                <li>• Processed Records: {result.processed_records}</li>
                <li>• Flagged Suspicious Entities: {result.generated_alerts_count}</li>
              </ul>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={!file || uploading}
          className="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white py-3 rounded-lg font-medium transition"
        >
          {uploading ? 'Processing & Scoring...' : 'Ingest & Run Models'}
        </button>
      </form>
    </div>
  );
};
