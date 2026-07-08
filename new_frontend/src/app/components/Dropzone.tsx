import React, { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';
import styles from './Dropzone.module.css';

export default function Dropzone({ onDrop }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onDrop(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onDrop(Array.from(e.target.files));
    }
  };

  return (
    <div 
      className={`${styles.dropzone} ${isDragOver ? styles.dragOver : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className={styles.iconCircle}>
        <UploadCloud size={28} />
      </div>
      <h3 className={styles.title}>Drop PDFs here</h3>
      <p className={styles.helper}>Drag and drop your files or click to browse your local machine.</p>
      
      <button 
        className={styles.browseBtn}
        onClick={() => fileInputRef.current?.click()}
      >
        Browse Files
      </button>
      
      <input 
        type="file" 
        multiple 
        accept="application/pdf"
        className={styles.hiddenInput}
        ref={fileInputRef}
        onChange={handleFileSelect}
      />
    </div>
  );
}
