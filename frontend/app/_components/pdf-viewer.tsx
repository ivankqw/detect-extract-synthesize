import React, { useState, useLayoutEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/20/solid";
import useResizeObserver from '@react-hook/resize-observer';
import { PDFViewerProps } from '../_types/types';
import { renderBoundingBoxes } from '../_utils/utils';
import { usePageNavigation } from '../_hooks/PageNavigationContext';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

// HOOKS
const useWidth = (target: React.RefObject<HTMLDivElement>) => {
  const [width, setWidth] = useState<number | undefined>(undefined);

  useLayoutEffect(() => {
    if (target.current) {
      setWidth(target.current.getBoundingClientRect().width);
    }
  }, [target]);

  useResizeObserver(target, (entry) => setWidth(entry.contentRect.width));
  return width;
};

const useHeight = (target: React.RefObject<HTMLDivElement>) => {
  const [height, setHeight] = useState<number | undefined>(undefined);

  useLayoutEffect(() => {
    if (target.current) {
      setHeight(target.current.getBoundingClientRect().height);
    }
  }, [target]);

  useResizeObserver(target, (entry) => setHeight(entry.contentRect.height));
  return height;
};


const PDFViewer: React.FC<PDFViewerProps> = ({
  file,
  pages_with_charts_idx,
  bboxes,
  numPages,
  doc_width,
  doc_height,
  onDocumentLoadSuccess,
  goToPreviousPage,
  goToNextPage,
}) => {
  const { pageNumber, navigateToPage } = usePageNavigation();
  const wrapperDiv = useRef(null);
  const width = useWidth(wrapperDiv);
  const height = useHeight(wrapperDiv);

  return (
    <div className="flex flex-col w-full">
      <div className="grid grid-cols-2 items-center justify-between w-full z-10 px-2">
        <div className="flex justify-start space-x-2">
          <button
            onClick={goToPreviousPage}
            disabled={pageNumber <= 1}
            className="px-2 text-gray-400 hover:text-gray-50 focus:z-20"
          >
            <span className="sr-only">Previous</span>
            <ChevronLeftIcon className="h-10 w-10" aria-hidden="true" />
          </button>
          <button
            onClick={goToNextPage}
            disabled={pageNumber >= numPages!}
            className="px-2 text-gray-400 hover:text-gray-50 focus:z-20"
          >
            <span className="sr-only">Next</span>
            <ChevronRightIcon className="h-10 w-10" aria-hidden="true" />
          </button>
        </div>
        <div className="flex justify-end">
          <p>Page {pageNumber} of {numPages}</p>
        </div>
      </div>
      <div className="wrapper" ref={wrapperDiv} style={{ position: 'relative' }}>
        <Document
          file={file}
          onLoadSuccess={onDocumentLoadSuccess}

        >
          <Page
            pageNumber={pageNumber}
            key={pageNumber}
            renderAnnotationLayer={false}
            renderTextLayer={false}
            width={width} // width: 90vw; max-width: 400px\
          >
            {renderBoundingBoxes(
              pageNumber,
              pages_with_charts_idx,
              bboxes,
              doc_width,
              doc_height,
              width,
              height
            )}
          </Page>
        </Document>
      </div>
    </div>
  );
};

export default PDFViewer;