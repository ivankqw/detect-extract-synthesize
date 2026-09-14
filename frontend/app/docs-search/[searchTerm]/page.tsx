'use client';

import React, { FC, useEffect, useState } from 'react';
import Navbar from '../../_components/navbar';
import Table from '../../_components/doc-table';
import { Document } from '../../_types/types';
import Spinner from '../../_components/spinner'; // Import a spinner component
import { useParams } from 'next/navigation';


const Page: FC = () => {
  const params = useParams<{ searchTerm: string }>();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch documents data from the backend
  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true); // Set loading to true when starting to fetch document data
      try {
        // Extract searchTerm from params
        const searchTerm = params.searchTerm;
        // Call the search endpoint with the searchTerm
        const response = await fetch(`/backend/docs-search/${searchTerm}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setDocuments(data.docs);
      } catch (error) {
        console.error("Fetching document data failed:", error);
      } finally {
        setLoading(false); // Set loading to false after fetching document data
      }
    };

    if (params.searchTerm) {
      fetchDocuments();
    }
  }, [params.searchTerm]); // Depend on params.searchTerm to re-run the effect when it changes

  if (loading) {
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

export default Page;
