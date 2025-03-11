'use client';

import { useEffect, useState } from 'react';
import Navbar from '../_components/navbar';
import Table from '../_components/doc-table';
import { Document } from '../_types/types';
import Spinner from '../_components/spinner'; // Import a spinner component

export default function Page() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true); // Add loading state

  // Fetch documents data from the backend
  useEffect(() => {
    const fetchDocuments = async () => {
      setIsLoading(true); // Start loading
      try {
        const response = await fetch('/backend/docs');
        const data = await response.json();
        setDocuments(data.docs);
      } catch (error) {
        console.error('Error fetching documents:', error);
      } finally {
        setIsLoading(false); // Stop loading regardless of the outcome
      }
    };

    fetchDocuments();
  }, []);

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-screen pt-20 bg-gray-100 dark:bg-gray-900">
          <Spinner />
        </div>
      </>
    )
  }

  return (
    <div>
      <Navbar />
      <Table documents={documents} />
    </div>
  );
}