import React, { useRef, useState, DragEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadTrafficFile } from '../services/api/ingest';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { CheckCircle2, AlertCircle, FileText } from 'lucide-react';

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
      setLocalError('Invalid file type. Please upload a CSV or JSON file.');
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

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-6">
        <CardTitle className="text-[32px] text-ink font-semibold tracking-apple-subhead">
          Ingest Telemetry
        </CardTitle>
        {mutation.isPending && <Badge variant="warning">Uploading...</Badge>}
        {mutation.isSuccess && <Badge variant="success">Ingest Complete</Badge>}
        {mutation.isError && <Badge variant="critical">Ingest Failed</Badge>}
      </CardHeader>
      <CardContent className="pt-8">
        <div 
          className={`rounded-apple-card p-12 text-center transition-colors cursor-pointer border relative z-10 ${
            isDragging 
              ? 'border-white bg-white/5' 
              : 'border-hairline hover:border-mid-gray bg-transparent'
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
          <FileText className="h-12 w-12 text-mid-gray mx-auto mb-4" strokeWidth={1.5} />
          
          {file ? (
            <div className="text-[14px] tracking-apple-body text-ink">
              <span className="font-semibold">{file.name}</span>
              <span className="text-mid-gray ml-2">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          ) : (
            <div>
              <p className="text-ink text-[14px] font-medium tracking-apple-body">Click to select or drag and drop</p>
              <p className="text-mid-gray text-[12px] tracking-apple-body mt-1">Supports .CSV, .JSON, .JSONL</p>
            </div>
          )}
        </div>
        
        <div className="mt-8 flex justify-end relative z-10">
          <button
            onClick={handleUpload}
            disabled={!file || mutation.isPending}
            className="flex items-center gap-2 px-6 py-2.5 bg-white text-black text-[14px] font-bold tracking-apple-body rounded-apple-pill hover:opacity-90 disabled:bg-cool-wash disabled:text-mid-gray disabled:cursor-not-allowed transition-all"
          >
            {mutation.isPending ? 'Processing...' : 'Ingest Logs'}
          </button>
        </div>
        
        {(localError || mutation.isError) && (
          <div className="mt-4 p-3 bg-red-950/30 border border-red-900/50 rounded-md text-sm text-red-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <p>{localError || 'Upload failed. Please check the backend connection.'}</p>
          </div>
        )}
        
        {mutation.isSuccess && mutation.data && (
          <div className="mt-4 p-3 bg-green-950/30 border border-green-900/50 rounded-md text-sm text-green-400 flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold">Processed successfully</p>
              <p className="text-green-500/80 mt-1 font-mono text-xs">
                File: {mutation.data.filename} | Records: {mutation.data.processed_records} | Alerts: {mutation.data.generated_alerts_count}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
