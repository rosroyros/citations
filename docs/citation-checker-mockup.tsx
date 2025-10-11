import React, { useState } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';

export default function CitationChecker() {
  const [activeTab, setActiveTab] = useState('paste');
  const [citations, setCitations] = useState('');
  const [fileName, setFileName] = useState('');

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFileName(file.name);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-8 h-8 text-purple-600" />
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">CitationCheck</h1>
            </div>
            <button className="text-purple-600 hover:text-purple-700 font-medium text-sm sm:text-base">
              Sign In
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 sm:pt-20 pb-8 sm:pb-12">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-3xl sm:text-5xl font-bold text-gray-900 mb-4 sm:mb-6">
            Stop spending 5 minutes fixing every citation
          </h2>
          <p className="text-lg sm:text-xl text-gray-600 mb-6 sm:mb-8">
            Citation generators create errors. We catch them. Get instant validation for your APA references and save hours of manual checking.
          </p>
          <div className="bg-purple-100 border border-purple-200 rounded-lg p-4 inline-block">
            <p className="text-purple-900 font-medium text-sm sm:text-base">
              <AlertCircle className="w-5 h-5 inline mr-2" />
              90.9% of papers contain formatting errors
            </p>
          </div>
        </div>
      </section>

      {/* Input Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8">
          {/* Tabs */}
          <div className="flex gap-2 sm:gap-4 mb-6 border-b">
            <button
              onClick={() => setActiveTab('paste')}
              className={`pb-3 px-3 sm:px-4 font-medium transition-colors text-sm sm:text-base ${
                activeTab === 'paste'
                  ? 'border-b-2 border-purple-600 text-purple-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Paste Text
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`pb-3 px-3 sm:px-4 font-medium transition-colors text-sm sm:text-base ${
                activeTab === 'upload'
                  ? 'border-b-2 border-purple-600 text-purple-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Upload className="w-4 h-4 inline mr-2" />
              Upload File
            </button>
          </div>

          {/* Paste Tab */}
          {activeTab === 'paste' && (
            <div>
              <label className="block text-gray-700 font-medium mb-3 text-sm sm:text-base">
                Paste your citations below (APA 7th edition)
              </label>
              <textarea
                value={citations}
                onChange={(e) => setCitations(e.target.value)}
                placeholder="Example:&#10;&#10;Smith, J., & Jones, M. (2023). Understanding research methods. Journal of Academic Studies, 45(2), 123-145. https://doi.org/10.1234/example&#10;&#10;Brown, A. (2022). Writing in APA style. Academic Press."
                className="w-full h-64 p-4 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none resize-none text-sm sm:text-base"
              />
              <p className="text-xs sm:text-sm text-gray-500 mt-2">
                Paste one or multiple citations. We'll check each one.
              </p>
            </div>
          )}

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div>
              <label className="block text-gray-700 font-medium mb-3 text-sm sm:text-base">
                Upload your document (.docx, .pdf)
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 sm:p-12 text-center hover:border-purple-400 transition-colors">
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".docx,.pdf"
                  onChange={handleFileUpload}
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 sm:w-16 sm:h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-base sm:text-lg font-medium text-gray-700 mb-2">
                    {fileName || 'Click to upload or drag and drop'}
                  </p>
                  <p className="text-xs sm:text-sm text-gray-500">
                    Word documents (.docx) or PDF files
                  </p>
                </label>
              </div>
            </div>
          )}

          {/* CTA Button */}
          <button className="w-full mt-6 bg-purple-600 hover:bg-purple-700 text-white font-bold py-4 px-6 rounded-lg transition-colors text-base sm:text-lg shadow-lg hover:shadow-xl">
            Check My Citations
          </button>

          {/* Feature Pills */}
          <div className="mt-6 flex flex-wrap gap-2 justify-center">
            <span className="bg-green-100 text-green-800 text-xs sm:text-sm px-3 py-1 rounded-full">
              ✓ Capitalization check
            </span>
            <span className="bg-green-100 text-green-800 text-xs sm:text-sm px-3 py-1 rounded-full">
              ✓ Italics validation
            </span>
            <span className="bg-green-100 text-green-800 text-xs sm:text-sm px-3 py-1 rounded-full">
              ✓ DOI formatting
            </span>
            <span className="bg-green-100 text-green-800 text-xs sm:text-sm px-3 py-1 rounded-full">
              ✓ Punctuation rules
            </span>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="bg-white py-12 sm:py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-2xl sm:text-3xl font-bold text-center text-gray-900 mb-8 sm:mb-12">
            Why students choose CitationCheck
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            <div className="text-center p-6">
              <div className="bg-purple-100 w-12 h-12 sm:w-16 sm:h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl sm:text-3xl">⚡</span>
              </div>
              <h4 className="font-bold text-lg sm:text-xl text-gray-900 mb-2">Save hours</h4>
              <p className="text-sm sm:text-base text-gray-600">
                Stop manually checking every citation. Get instant validation in seconds.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="bg-purple-100 w-12 h-12 sm:w-16 sm:h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl sm:text-3xl">🎯</span>
              </div>
              <h4 className="font-bold text-lg sm:text-xl text-gray-900 mb-2">Catch generator errors</h4>
              <p className="text-sm sm:text-base text-gray-600">
                EasyBib, Zotero, and others make mistakes. We find them before your professor does.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="bg-purple-100 w-12 h-12 sm:w-16 sm:h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl sm:text-3xl">✅</span>
              </div>
              <h4 className="font-bold text-lg sm:text-xl text-gray-900 mb-2">Never lose points</h4>
              <p className="text-sm sm:text-base text-gray-600">
                Submit with confidence. No more losing grades on formatting mistakes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 sm:py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid sm:grid-cols-3 gap-8">
            <div>
              <h5 className="font-bold mb-3 text-sm sm:text-base">Product</h5>
              <ul className="space-y-2 text-xs sm:text-sm text-gray-400">
                <li>How it works</li>
                <li>Pricing</li>
                <li>APA 7th Guide</li>
              </ul>
            </div>
            <div>
              <h5 className="font-bold mb-3 text-sm sm:text-base">Support</h5>
              <ul className="space-y-2 text-xs sm:text-sm text-gray-400">
                <li>Help Center</li>
                <li>Contact Us</li>
                <li>Citation Examples</li>
              </ul>
            </div>
            <div>
              <h5 className="font-bold mb-3 text-sm sm:text-base">Company</h5>
              <ul className="space-y-2 text-xs sm:text-sm text-gray-400">
                <li>About</li>
                <li>Privacy Policy</li>
                <li>Terms of Service</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-xs sm:text-sm text-gray-400">
            <p>© 2025 CitationCheck. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}