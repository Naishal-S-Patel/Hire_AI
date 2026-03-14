import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, X } from 'lucide-react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

const ResumeViewer = ({ url, onClose }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
  };

  const onDocumentLoadError = (err) => {
    setError('Failed to load PDF. The file may not be available.');
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-50 rounded-xl shadow-2xl border border-border/60 flex flex-col w-full max-w-4xl max-h-[95vh]">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/60 bg-white rounded-t-xl">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPageNumber(p => Math.max(1, p - 1))}
              disabled={pageNumber <= 1}
              className="p-1.5 rounded-lg hover:bg-gray-700 disabled:opacity-40 transition-colors text-slate-700"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="text-sm text-slate-600 min-w-[80px] text-center">
              {loading ? '...' : `${pageNumber} / ${numPages || '?'}`}
            </span>
            <button
              onClick={() => setPageNumber(p => Math.min(numPages || 1, p + 1))}
              disabled={pageNumber >= (numPages || 1)}
              className="p-1.5 rounded-lg hover:bg-gray-700 disabled:opacity-40 transition-colors text-slate-700"
            >
              <ChevronRight size={18} />
            </button>
            <div className="w-px h-5 bg-gray-600 mx-1" />
            <button
              onClick={() => setScale(s => Math.max(0.5, s - 0.2))}
              className="p-1.5 rounded-lg hover:bg-gray-700 transition-colors text-slate-700"
            >
              <ZoomOut size={18} />
            </button>
            <span className="text-sm text-slate-600 w-12 text-center">{Math.round(scale * 100)}%</span>
            <button
              onClick={() => setScale(s => Math.min(2.5, s + 0.2))}
              className="p-1.5 rounded-lg hover:bg-gray-700 transition-colors text-slate-700"
            >
              <ZoomIn size={18} />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 text-sm bg-primary hover:bg-primary/90 text-foreground rounded-lg transition-colors"
            >
              Open in New Tab
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-gray-700 transition-colors text-slate-600"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* PDF Content */}
        <div className="flex-1 overflow-auto flex items-start justify-center p-4 bg-white">
          {error ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <p className="text-sm">{error}</p>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 px-4 py-2 bg-primary text-foreground rounded-lg text-sm hover:bg-primary/90"
              >
                Open PDF directly
              </a>
            </div>
          ) : (
            <Document
              file={url}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex items-center justify-center h-64">
                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              }
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                className="shadow-lg"
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
            </Document>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResumeViewer;
