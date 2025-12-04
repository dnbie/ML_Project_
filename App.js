import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [documentsUploaded, setDocumentsUploaded] = useState(false);
  const [documentInfo, setDocumentInfo] = useState(null);

  const handleUploadSuccess = (info) => {
    setDocumentInfo(info);
    setDocumentsUploaded(true);
  };

  const handleReset = () => {
    setDocumentsUploaded(false);
    setDocumentInfo(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📄 Document Intelligence Assistant</h1>
        <p>Advanced document analysis using AI</p>
      </header>

      <main className="App-main">
        {!documentsUploaded ? (
          <FileUpload onUploadSuccess={handleUploadSuccess} />
        ) : (
          <ChatInterface documentInfo={documentInfo} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}

export default App;
