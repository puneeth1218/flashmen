import React, { useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadTrafficFile } from '../services/api/ingest';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { UploadCloud, CheckCircle2, AlertCircle } from 'lucide-react';

export const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: uploadTrafficFile,
    onSuccess: () => {
      // Invalidate queries so that the AlertTable re-fetches
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (file) {
      mutation.mutate(file);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Ingest Telemetry Data</CardTitle>
        {mutation.isPending && <Badge variant="warning">Uploading...</Badge>}
        {mutation.isSuccess && <Badge variant="success">Ingest Complete</Badge>}
        {mutation.isError && <Badge variant="critical">Ingest Failed</Badge>}
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <input
            type="file"
            accept=".csv,.json"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="block w-full text-sm text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-zinc-800 file:text-zinc-300 hover:file:bg-zinc-700 focus:outline-none focus:ring-2 focus:ring-zinc-400 transition-colors"
          />
          <button
            onClick={handleUpload}
            disabled={!file || mutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-100 text-zinc-950 text-sm font-semibold rounded-md hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
          >
            <UploadCloud className="h-4 w-4" />
            Upload
          </button>
        </div>
        
        {mutation.isSuccess && mutation.data && (
          <div className="mt-4 p-3 bg-green-950/30 border border-green-900/50 rounded-md text-sm text-green-400 flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold">Processed successfully</p>
              <p className="text-green-500/80">
                File: {mutation.data.filename} - Processed {mutation.data.processed_records} records, generated {mutation.data.generated_alerts_count} alerts.
              </p>
            </div>
          </div>
        )}
        
        {mutation.isError && (
          <div className="mt-4 p-3 bg-red-950/30 border border-red-900/50 rounded-md text-sm text-red-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <p>Upload failed. Please check the file format and ensure the backend is running.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
