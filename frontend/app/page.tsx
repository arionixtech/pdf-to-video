'use client';

import { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== 'application/pdf') {
        setError('Please select a PDF file');
        return;
      }
      if (selectedFile.size > 50 * 1024 * 1024) {
        setError('File too large. Maximum 50MB');
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const uploadFile = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setJobId(response.data.job_id);
      startPolling(response.data.job_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
      setUploading(false);
    }
  };

  const startPolling = (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/api/status/${id}`);
        setStatus(response.data);

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          clearInterval(interval);
          setUploading(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);
  };

  const downloadVideo = () => {
    if (jobId) {
      window.open(`${API_URL}/api/video/${jobId}`, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-white mb-4">
              📄 PDF to Video
            </h1>
            <p className="text-xl text-white opacity-90">
              Transform your PDFs into engaging animated videos
            </p>
          </div>

          {/* Upload Card */}
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            {!jobId ? (
              <div>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-purple-500 transition-colors">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer"
                  >
                    <div className="text-6xl mb-4">📤</div>
                    <div className="text-lg font-semibold mb-2">
                      Click to upload PDF
                    </div>
                    <div className="text-sm text-gray-500">
                      Maximum file size: 50MB
                    </div>
                  </label>
                </div>

                {file && (
                  <div className="mt-6">
                    <div className="bg-gray-100 rounded-lg p-4 mb-4">
                      <div className="font-semibold">{file.name}</div>
                      <div className="text-sm text-gray-600">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>

                    <button
                      onClick={uploadFile}
                      disabled={uploading}
                      className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {uploading ? 'Uploading...' : 'Convert to Video'}
                    </button>
                  </div>
                )}

                {error && (
                  <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                    {error}
                  </div>
                )}
              </div>
            ) : (
              <div>
                {/* Processing Status */}
                {status && (
                  <div>
                    <div className="mb-6">
                      <div className="flex justify-between mb-2">
                        <span className="font-semibold">Processing...</span>
                        <span>{status.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className="bg-purple-600 h-3 rounded-full transition-all duration-300"
                          style={{ width: `${status.progress}%` }}
                        />
                      </div>
                    </div>

                    <div className="text-sm text-gray-600 mb-4">
                      Status: <span className="font-semibold">{status.status}</span>
                    </div>

                    {status.status === 'completed' && (
                      <div>
                        <div className="bg-green-100 border border-green-400 text-green-700 p-4 rounded-lg mb-4">
                          ✅ Video generated successfully!
                        </div>
                        <button
                          onClick={downloadVideo}
                          className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 transition-colors"
                        >
                          Download Video
                        </button>
                        <button
                          onClick={() => {
                            setJobId(null);
                            setStatus(null);
                            setFile(null);
                          }}
                          className="w-full mt-3 bg-gray-200 text-gray-700 py-2 px-6 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                        >
                          Convert Another PDF
                        </button>
                      </div>
                    )}

                    {status.status === 'failed' && (
                      <div>
                        <div className="bg-red-100 border border-red-400 text-red-700 p-4 rounded-lg mb-4">
                          ❌ Processing failed: {status.error}
                        </div>
                        <button
                          onClick={() => {
                            setJobId(null);
                            setStatus(null);
                            setFile(null);
                          }}
                          className="w-full bg-gray-200 text-gray-700 py-2 px-6 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                        >
                          Try Again
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Info Section */}
          <div className="mt-12 text-center text-white">
            <h2 className="text-2xl font-bold mb-4">How it works</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white bg-opacity-20 rounded-lg p-6">
                <div className="text-4xl mb-2">📄</div>
                <div className="font-semibold mb-1">1. Upload PDF</div>
                <div className="text-sm opacity-90">Upload your educational PDF</div>
              </div>
              <div className="bg-white bg-opacity-20 rounded-lg p-6">
                <div className="text-4xl mb-2">⚙️</div>
                <div className="font-semibold mb-1">2. AI Processing</div>
                <div className="text-sm opacity-90">AI creates animated video</div>
              </div>
              <div className="bg-white bg-opacity-20 rounded-lg p-6">
                <div className="text-4xl mb-2">🎬</div>
                <div className="font-semibold mb-1">3. Download</div>
                <div className="text-sm opacity-90">Get your animated video</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
