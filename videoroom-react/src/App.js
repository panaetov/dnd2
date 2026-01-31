import React, { useEffect, useState } from 'react';
import VideoRoom from './components/VideoRoom';
import './App.css';

function App() {
  const [janusLoaded, setJanusLoaded] = useState(false);

  useEffect(() => {
    // Load webrtc-adapter first
    const adapterScript = document.createElement('script');
    adapterScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/webrtc-adapter/9.0.3/adapter.min.js';
    adapterScript.async = true;
    
    // Load janus.js script after adapter
    const script = document.createElement('script');
    script.src = '/janus.js';
    script.async = true;
    
    adapterScript.onload = () => {
      // Wait a bit for adapter to initialize navigator.mediaDevices polyfill
      setTimeout(() => {
        script.onload = () => {
          if (window.Janus) {
            setJanusLoaded(true);
          }
        };
        document.body.appendChild(script);
      }, 100);
    };
    
    adapterScript.onerror = () => {
      console.error('Failed to load webrtc-adapter');
      // Still try to load janus.js
      script.onload = () => {
        if (window.Janus) {
          setJanusLoaded(true);
        }
      };
      document.body.appendChild(script);
    };
    
    document.body.appendChild(adapterScript);

    // Load toastr and bootbox
    const toastrScript = document.createElement('script');
    toastrScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/toastr.js/2.1.4/toastr.min.js';
    document.body.appendChild(toastrScript);

    const bootboxScript = document.createElement('script');
    bootboxScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/bootbox.js/6.0.0/bootbox.min.js';
    document.body.appendChild(bootboxScript);

    // Load Bootstrap JS
    const bootstrapScript = document.createElement('script');
    bootstrapScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.2/js/bootstrap.bundle.min.js';
    document.body.appendChild(bootstrapScript);

    return () => {
      if (document.body.contains(adapterScript)) {
        document.body.removeChild(adapterScript);
      }
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
      if (document.body.contains(toastrScript)) {
        document.body.removeChild(toastrScript);
      }
      if (document.body.contains(bootboxScript)) {
        document.body.removeChild(bootboxScript);
      }
      if (document.body.contains(bootstrapScript)) {
        document.body.removeChild(bootstrapScript);
      }
    };
  }, []);

  if (!janusLoaded) {
    return (
      <div className="container mt-5">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Loading Janus library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <VideoRoom />
    </div>
  );
}

export default App;
