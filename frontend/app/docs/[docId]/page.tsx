'use client';

import React, { FC, useEffect, useState, useCallback, useMemo } from 'react';
import PDFViewer from "../../_components/pdf-viewer";
import { useCompletion } from "ai/react";
import Navbar from "../../_components/navbar";
import Chat from "../../_components/chat";
import { DocumentData, DocumentLoadSuccessParams } from "../../_types/types";
import { PageNavigationContext } from '../../_hooks/PageNavigationContext';
import { useParams } from 'next/navigation';


const Page: FC = () => {
  const params = useParams<{ docId: string }>();
  // STATES
  const [docData, setDocData] = useState<DocumentData | null>(null);
  const [numPages, setNumPages] = useState<number>(); // Total number of pages in the PDF
  const [pageNumber, setPageNumber] = useState<number>(1); // Current page number
  const [loading, setLoading] = useState(true); // Loading state

  // CONSTANTS
  const pdfFileUrl = `/backend/getpdf/${params.docId}`;

  // CALLBACKS to pass into the PDFViewer component
  const onDocumentLoadSuccess = useCallback(({ numPages }: DocumentLoadSuccessParams) => {
    setNumPages(numPages);
    setLoading(false); // Set loading to false when the document is loaded
  }, []);

  const goToPreviousPage = useCallback(() => {
    setPageNumber((prevPageNumber) => Math.max(prevPageNumber - 1, 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setPageNumber((prevPageNumber) => (numPages ? Math.min(prevPageNumber + 1, numPages) : prevPageNumber));
  }, [numPages]);

  const navigateToPage = useCallback((page: number) => {
    setPageNumber(page);
  }, []);

  // Memoize the props to avoid unnecessary re-renders
  const pdfViewerProps = useMemo(() => ({
    pageNumber,
    numPages,
    onDocumentLoadSuccess,
    goToPreviousPage,
    goToNextPage,
  }), [pageNumber, numPages, onDocumentLoadSuccess, goToPreviousPage, goToNextPage]);

  useEffect(() => {
    const fetchDocData = async () => {
      setLoading(true); // Set loading to true when starting to fetch document data
      try {
        const response = await fetch(`/backend/docs/${params.docId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setDocData(data);
      } catch (error) {
        console.error("Fetching document data failed:", error);
      } finally {
        setLoading(false); // Set loading to false after fetching document data
      }
    };

    fetchDocData();
  }, [params.docId]); // Empty dependency array ensures this effect runs only once

  // Assuming useCompletion is a custom hook you've defined
  const { input, completion, handleInputChange, handleSubmit } = useCompletion({
    api: "/backend/ask", // Update the API endpoint if necessary
    headers: {
      "Content-Type": "application/json",
    },
  });

  return (
    <PageNavigationContext.Provider value={{ pageNumber, navigateToPage }}>
      <div className="h-screen">
        <Navbar />
        <div className="flex dark:bg-gray-800 dark:text-white h-full dark:bg-gray-900">
          <div className="flex flex-col w-1/2">
            {loading ? (
              <div className="flex justify-center items-center">
                <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M12 2c-1.1 0-2 .9-2 2v8h4V4c0-1.1-.9-2-2-2z"></path>
                </svg>
                Loading document...
              </div>
            ) : (
              <div className="p-5">
                <p className="text-lg font-semibold text-gray-800 dark:text-white mt-4 mb-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg shadow">
                  {JSON.stringify(docData?.doc.name)}
                </p>
                <PDFViewer {...pdfViewerProps}
                  file={pdfFileUrl}
                  bboxes={docData?.doc.bboxes}
                  pages_with_charts_idx={docData?.doc.pages_with_charts_idx}
                  doc_width={docData?.doc.width || 0}
                  doc_height={docData?.doc.height || 0}
                />
              </div>
            )}
          </div>
          <div className="w-1/2 h-full">
            <Chat docId={params.docId} />
          </div>
        </div>
      </div>
    </PageNavigationContext.Provider>
  );
}

export default Page;