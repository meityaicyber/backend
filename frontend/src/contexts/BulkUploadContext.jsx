import React, { createContext, useState, useContext } from 'react';
import { useSnackbar } from 'notistack';
import api from '../api/axios';

const BulkUploadContext = createContext();

export const useBulkUpload = () => useContext(BulkUploadContext);

export const BulkUploadProvider = ({ children }) => {
  const { enqueueSnackbar } = useSnackbar();

  const [bulkFilesData, setBulkFilesData] = useState([]);
  const [bulkProgress, setBulkProgress] = useState(0);
  const [bulkTotal, setBulkTotal] = useState(0);
  const [bulkRunning, setBulkRunning] = useState(false);
  const [bulkFinished, setBulkFinished] = useState(false);
  const [bulkStartTime, setBulkStartTime] = useState(null);
  const [bulkEndTime, setBulkEndTime] = useState(null);
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const [isWidgetMinimized, setIsWidgetMinimized] = useState(false);

  const updateFileStatus = (id, status, details) => {
    setBulkFilesData(prev => prev.map(item => 
      item.id === id ? { ...item, status, details } : item
    ));
  };

  const startBulkUpload = async (filesData, passwordMap, selectedAgency, concurrency) => {
    setBulkRunning(true);
    setBulkFinished(false);
    setBulkProgress(0);
    setBulkTotal(filesData.length);
    setBulkStartTime(Date.now());
    setBulkEndTime(null);
    setIsWidgetOpen(true);
    setIsWidgetMinimized(false);

    // Initial state setup
    setBulkFilesData(filesData.map(item => ({...item, status: 'Pending', details: '-'})));

    let currentIndex = 0;

    const processNext = async () => {
      let localIndex;
      
      // Need a way to safely read the latest bulkFilesData length, but we know it's filesData.length
      localIndex = currentIndex++;
      if (localIndex >= filesData.length) return;
      
      const fileData = filesData[localIndex];
      const file = fileData.file;
      const cleanName = fileData.name;
      const baseName = cleanName.replace(/\.[^/.]+$/, "");
      const matchedPassword = passwordMap[baseName.toLowerCase()] || passwordMap[cleanName.toLowerCase()] || '';

      let reportId = null;

      try {
        updateFileStatus(fileData.id, 'Uploading', 'Uploading to storage...');

        const formData = new FormData();
        formData.append('file', file, cleanName);
        if (selectedAgency) formData.append('agency_id', selectedAgency);
        if (matchedPassword) formData.append('file_password', matchedPassword);

        // 1. Upload
        const uploadRes = await api.post('/api/reports/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        reportId = uploadRes.data.report_id;

        // 2. Run Pipeline
        updateFileStatus(fileData.id, 'Pipeline', 'Running AI Pipeline...');
        await api.post(`/api/reports/${reportId}/run-pipeline`);
        
        updateFileStatus(fileData.id, 'Success', 'File saved and pipeline completed.');
      } catch (err) {
        let msg = 'Operation failed';
        if (err.response) {
          if (err.response.data && typeof err.response.data.detail === 'string') {
            msg = err.response.data.detail;
          } else if (err.response.data && Array.isArray(err.response.data.detail)) {
            msg = err.response.data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
          } else if (err.response.status === 413) {
            msg = "File size limit exceeded";
          } else if (err.response.status === 500) {
             // If there's a specific message in the response text, try to use it
             if (typeof err.response.data === 'string' && err.response.data.length < 200 && !err.response.data.includes('<html')) {
                msg = err.response.data;
             } else {
                msg = "Internal server error on backend";
             }
          } else {
            msg = `Request failed with status code ${err.response.status}`;
          }
        } else {
          msg = err.message || 'Network error';
        }
        
        if (reportId) {
          updateFileStatus(fileData.id, 'Failed', `${msg} (Rolling back...)`);
          // Rollback: delete from system
          try {
             await api.delete(`/api/reports/${reportId}`);
             updateFileStatus(fileData.id, 'Failed', `${msg}. File deleted from system.`);
          } catch(rollbackErr) {
             updateFileStatus(fileData.id, 'Failed', `${msg}. Rollback failed: ${rollbackErr.message}`);
          }
        } else {
          updateFileStatus(fileData.id, 'Failed', msg);
        }
      }
      
      setBulkProgress(prev => prev + 1);
      await processNext();
    };

    const workers = [];
    for (let i = 0; i < concurrency; i++) {
      workers.push(processNext());
    }
    
    await Promise.all(workers);
    
    setBulkEndTime(Date.now());
    setBulkRunning(false);
    setBulkFinished(true);
    enqueueSnackbar('Bulk processing completed', {variant: 'success'});
  };

  const closeWidget = () => {
    setIsWidgetOpen(false);
  };

  const toggleMinimize = () => {
    setIsWidgetMinimized(prev => !prev);
  };

  const resetBulkState = () => {
     setBulkFilesData([]);
     setBulkProgress(0);
     setBulkTotal(0);
     setBulkRunning(false);
     setBulkFinished(false);
     setBulkStartTime(null);
     setBulkEndTime(null);
     setIsWidgetOpen(false);
  };

  return (
    <BulkUploadContext.Provider value={{
      bulkFilesData, setBulkFilesData, bulkProgress, bulkTotal, bulkRunning, bulkFinished, setBulkFinished,
      bulkStartTime, bulkEndTime, isWidgetOpen, isWidgetMinimized,
      startBulkUpload, closeWidget, toggleMinimize, resetBulkState
    }}>
      {children}
    </BulkUploadContext.Provider>
  );
};
