// src/components/shared/FileUpload.tsx

'use client';

import React, { useCallback, useState } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { FileUploadState } from '@/types';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSizeMB?: number;
  uploadState?: FileUploadState;
  className?: string;
}

export function FileUpload({
  onFileSelect,
  accept = '.pdf,.png,.jpg,.jpeg',
  maxSizeMB = 10,
  uploadState,
  className,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    setLocalError(null);
    
    const maxBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxBytes) {
      setLocalError(`File size must be less than ${maxSizeMB}MB`);
      return false;
    }

    const allowedTypes = accept.split(',').map(t => t.trim().toLowerCase());
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      setLocalError(`File type not supported. Allowed: ${accept}`);
      return false;
    }

    return true;
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        onFileSelect(file);
      }
    }
  }, [onFileSelect]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        onFileSelect(file);
      }
    }
  };

  const error = localError || uploadState?.error;
  const status = uploadState?.status || 'idle';

  return (
    <div className={cn('w-full', className)}>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={cn(
          'relative border-2 border-dashed rounded-xl p-8 text-center transition-all',
          dragActive && 'border-blue-500 bg-blue-50',
          error && 'border-red-300 bg-red-50',
          status === 'complete' && 'border-green-300 bg-green-50',
          !dragActive && !error && status !== 'complete' && 'border-gray-300 hover:border-gray-400 bg-gray-50'
        )}
      >
        <input
          type="file"
          accept={accept}
          onChange={handleChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={status === 'uploading' || status === 'processing'}
        />

        {status === 'idle' && !uploadState?.file && (
          <div className="space-y-3">
            <div className="mx-auto w-12 h-12 flex items-center justify-center bg-gray-100 rounded-full">
              <Upload className="w-6 h-6 text-gray-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">
                Drag and drop your file here, or click to browse
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Supports {accept} up to {maxSizeMB}MB
              </p>
            </div>
          </div>
        )}

        {(status === 'uploading' || status === 'processing') && (
          <div className="space-y-3">
            <Loader2 className="w-8 h-8 mx-auto text-blue-500 animate-spin" />
            <div>
              <p className="text-sm font-medium text-gray-700">
                {status === 'uploading' ? 'Uploading...' : 'Processing...'}
              </p>
              {uploadState?.progress !== undefined && (
                <div className="mt-2 w-48 mx-auto bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${uploadState.progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {status === 'complete' && uploadState?.file && (
          <div className="space-y-3">
            <CheckCircle className="w-8 h-8 mx-auto text-green-500" />
            <div className="flex items-center justify-center gap-2">
              <File className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">
                {uploadState.file.name}
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 flex items-center justify-center gap-2 text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}