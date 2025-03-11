// This is for display in table
export interface Document {
    id: string;
    name: string;
    path: string;
    pages_with_charts_idx: number[];
    bboxes: number[][][]; // Assuming bboxes is an array of arrays of arrays of numbers
}

// info for PDF viewer
export interface DocumentData {
    doc: {
        pages_with_charts_idx: number[];
        id: string;
        bboxes: number[][][];
        name: string;
        path: string;
        parsed_data: string;
        width: number | undefined;
        height: number | undefined;
    };
}

export interface PageProps {
    params: {
        docId: string;
    };
}

// for PDF viewer
export interface DocumentLoadSuccessParams {
    numPages: number;
}

export interface PDFViewerProps {
    file: string;
    pages_with_charts_idx: number[] | undefined;
    bboxes: number[][][] | undefined;
    pageNumber: number;
    numPages: number | undefined;
    doc_width: number;
    doc_height: number;
    onDocumentLoadSuccess: ({ numPages }: { numPages: number }) => void;
    goToPreviousPage: () => void;
    goToNextPage: () => void;
}
