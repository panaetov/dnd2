// Polyfill for navigator.mediaDevices on HTTP (for development)
// This allows getUserMedia to work on HTTP by using the legacy API
if (!navigator.mediaDevices) {
  navigator.mediaDevices = {};
}

if (!navigator.mediaDevices.getUserMedia) {
  navigator.mediaDevices.getUserMedia = function(constraints) {
    // Use legacy getUserMedia API as fallback
    const getUserMedia = navigator.getUserMedia || 
                        navigator.webkitGetUserMedia || 
                        navigator.mozGetUserMedia || 
                        navigator.msGetUserMedia;
    
    if (!getUserMedia) {
      return Promise.reject(new Error('getUserMedia is not supported in this browser'));
    }
    
    return new Promise(function(resolve, reject) {
      getUserMedia.call(navigator, constraints, resolve, reject);
    });
  };
}

if (!navigator.mediaDevices.getDisplayMedia) {
  navigator.mediaDevices.getDisplayMedia = function(constraints) {
    return Promise.reject(new Error('getDisplayMedia is not available on HTTP. Please use HTTPS.'));
  };
}

if (!navigator.mediaDevices.enumerateDevices) {
  navigator.mediaDevices.enumerateDevices = function() {
    // Fallback for enumerateDevices - return empty array or use legacy API if available
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
      return navigator.mediaDevices.enumerateDevices();
    }
    // Return empty array as fallback
    return Promise.resolve([]);
  };
}

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
