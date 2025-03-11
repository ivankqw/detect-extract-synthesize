import React from 'react';
import Link from 'next/link';
import { DocumentTextIcon } from "@heroicons/react/20/solid";
import { Document } from '../_types/types';

interface TableProps {
  documents: Document[];
}

const Table: React.FC<TableProps> = ({ documents }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Documents</h1>
      <div className="overflow-x-auto relative">
        <table className="w-full font-medium text-left rtl:text-right text-gray-500 dark:text-gray-400">
          <thead className="font-medium text-gray-700 uppercase bg-gray-200 dark:bg-gray-700 dark:text-gray-300">
            <tr>
              <th scope="col" className="px-6 py-3">Name</th>
              <th scope="col" className="px-6 py-3">Go to Document</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} className="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-600">
                <td className="px-6 py-4 dark:text-white">
                  {doc.name}
                </td>
                <td className="px-6 py-4 text-center">
                  <Link href={`/docs/${doc.id}`} className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-500">
                    <DocumentTextIcon className="h-6 w-6 inline-block" aria-hidden="true" />
                  </Link>
                </td>
              </tr>

            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Table;