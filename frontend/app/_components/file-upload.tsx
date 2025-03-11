'use client'

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';


export default function FileUpload() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null); // State to hold the error message
  const [isProcessing, setIsProcessing] = useState(false); // State to hold the processing status


  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const uploadFile = async () => {
    if (selectedFile) {
      setIsLoading(true);
      setError(''); // Clear any previous error message
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const response = await fetch('/backend/upload', {
          method: 'POST',
          body: formData,
          // Remove the AbortController logic if you are not using it elsewhere
        });

        const result = await response.json();
        setIsLoading(false);

        if (result.status === 'success') {
          console.log('File uploaded successfully, UID:', result.uid);
          setIsProcessing(true); // Set processing to true
          checkUploadStatus(result.uid); // Start polling for the upload status
        } else {
          setError(result.message);
        }
      } catch (error) {
        setIsLoading(false);
        setError('An unexpected error occurred');
      }
    }
  };

  const maxRetries = 10; // Maximum number of retries
  const retryInterval = 5000; // Time to wait between retries in milliseconds
  const statusCheckInterval = 10000; // Time to wait between status checks in milliseconds

  const checkUploadStatus = async (uid: string, retries = maxRetries) => {
    try {
      const response = await fetch(`/backend/upload-status/${uid}`);
      const statusResult = await response.json();

      if (statusResult.status === 'success' && statusResult.is_parsed) {
        // clearInterval(statusCheckInterval);
        console.log('File processing complete. Redirecting to:', `/docs/${uid}`);
        router.push(`/docs/${uid}`);
        // Reset states after successful processing
        setIsProcessing(false);
        setSelectedFile(null); // Assuming you want to clear the selected file as well
        setError(null); // Clear any error messages
      } else if (statusResult.status === 'error') {
        throw new Error(statusResult.message);
      } else {
        setTimeout(() => checkUploadStatus(uid, maxRetries), statusCheckInterval);
      }
    } catch (error) {
      if (retries > 0) {
        console.error(`Attempt ${maxRetries - retries + 1} failed. Retrying in ${retryInterval / 1000} seconds...`, error);
        setTimeout(() => checkUploadStatus(uid, retries - 1), retryInterval);
      } else {
        setIsProcessing(false);
        // Reset states after failing all retries
        setSelectedFile(null); // Assuming you want to clear the selected file as well
        setIsLoading(false); // Stop the loading state
      }
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 justify-center items-center">
      {isProcessing && (
        <div className="fixed top-0 left-0 right-0 p-4 bg-blue-100 border-t-4 border-blue-500 dark:bg-blue-800 dark:border-blue-600">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {/* Spinner Icon */}
              <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0116 0H4z"></path>
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-blue-700 dark:text-blue-200">
                Processing your file, please wait...
              </p>
            </div>
          </div>
        </div>
      )}
      <div className="w-full max-w-md p-6 bg-gray-800 rounded-lg shadow-md">
        {error && (
          <div className="mb-4 p-4 bg-red-600 text-white rounded relative" role="alert">
            <strong className="font-bold">Error! </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        <div className="flex flex-col items-center">
          <label
            htmlFor="file_upload"
            className="mb-4 w-full flex flex-col items-center px-4 py-6 bg-gray-700 text-blue-200 rounded-lg tracking-wide uppercase border border-blue-300 cursor-pointer hover:bg-gray-600 hover:text-blue-100"
          >
            <svg className="w-8 h-8" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
              <path d="M16.7,5.3l-1.9-2c-0.2-0.2-0.5-0.3-0.8-0.3H5C4.4,3,4,3.4,4,4v12c0,0.6,0.4,1,1,1h10c0.6,0,1-0.4,1-1V6.1
              C16,5.8,16.9,5.5,16.7,5.3z M11,15c-1.7,0-3-1.3-3-3s1.3-3,3-3s3,1.3,3,3S12.7,15,11,15z M14,7h-3V4h3V7z"/>
            </svg>
            <span className="mt-2 text-base leading-normal">Select a file</span>
            <input
              id="file_upload"
              type="file"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
          <button
            onClick={uploadFile}
            className={`mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg tracking-wide uppercase border border-blue-300 cursor-pointer hover:bg-blue-500 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            disabled={!selectedFile || isLoading || isProcessing}
          >
            {isLoading || isProcessing ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M12 2c-1.1 0-2 .9-2 2v8h4V4c0-1.1-.9-2-2-2z"></path>
                </svg>
                Processing...
              </>
            ) : 'Upload'}
          </button>
        </div>
        {selectedFile && (
          <div className="mt-2 text-center text-sm text-gray-400">
            File selected: <span className="text-blue-200">{selectedFile.name}</span>
          </div>
        )}
      </div>
    </div>
  );
}