import React, { useEffect, useRef } from 'react';
import './VideoCard.css';

const VideoCard = ({
  title,
  badge,
  badgeClass,
  id,
  localTracks,
  localVideos,
  feed,
  bitrate,
  onBitrateChange,
  onToggleMute,
  onUnpublish,
  sfutest,
  bitrateTimers,
  setBitrateTimers,
  isMuted
}) => {
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const containerRef = useRef(null);
  const bitrateIntervalRef = useRef(null);
  const resolutionRef = useRef(null);
  const bitrateDisplayRef = useRef(null);

  const isLocal = id === 'local';

  // Handle local video tracks
  useEffect(() => {
    if (!isLocal || !videoRef.current) return;

    const videoElement = videoRef.current;
    const trackIds = Object.keys(localTracks);
    
    // Remove all existing video elements
    const existingVideos = containerRef.current?.querySelectorAll('video');
    existingVideos?.forEach(v => {
      if (v.id.startsWith('myvideo')) {
        v.remove();
      }
    });

    // Add new video elements for each track
    trackIds.forEach(trackId => {
      const stream = localTracks[trackId];
      if (stream && stream.getVideoTracks().length > 0) {
        const videoId = `myvideo${trackId}`;
        let videoEl = document.getElementById(videoId);
        
        if (!videoEl) {
          videoEl = document.createElement('video');
          videoEl.id = videoId;
          videoEl.className = 'rounded centered';
          videoEl.style.width = '100%';
          videoEl.autoplay = true;
          videoEl.playsInline = true;
          videoEl.muted = true;
          containerRef.current?.prepend(videoEl);
        }
        
        if (window.Janus) {
          window.Janus.attachMediaStream(videoEl, stream);
        }
      }
    });

    // Show/hide no video placeholder
    const noVideoContainer = containerRef.current?.querySelector('.no-video-container');
    if (localVideos === 0) {
      if (!noVideoContainer) {
        const placeholder = document.createElement('div');
        placeholder.className = 'no-video-container';
        placeholder.innerHTML = `
          <i class="fa-solid fa-video fa-xl no-video-icon"></i>
          <span class="no-video-text">No webcam available</span>
        `;
        containerRef.current?.prepend(placeholder);
      }
    } else {
      noVideoContainer?.remove();
    }
  }, [localTracks, localVideos, isLocal]);

  // Handle remote feed tracks
  useEffect(() => {
    if (isLocal || !feed || !containerRef.current) return;

    const container = containerRef.current;
    
    // Clear existing media elements
    const existingMedia = container.querySelectorAll('video, audio');
    existingMedia.forEach(el => el.remove());

    // Add remote tracks
    const trackMids = Object.keys(feed.remoteTracks || {});
    trackMids.forEach(mid => {
      const stream = feed.remoteTracks[mid];
      if (!stream) return;

      const tracks = stream.getTracks();
      tracks.forEach(track => {
        if (track.kind === 'audio') {
          const audioId = `remotevideo${feed.rfindex}-${mid}`;
          let audioEl = document.getElementById(audioId);
          if (!audioEl) {
            audioEl = document.createElement('audio');
            audioEl.id = audioId;
            audioEl.className = 'hide';
            audioEl.autoplay = true;
            audioEl.playsInline = true;
            container.appendChild(audioEl);
          }
          if (window.Janus) {
            window.Janus.attachMediaStream(audioEl, stream);
          }
        } else if (track.kind === 'video') {
          const videoId = `remotevideo${feed.rfindex}-${mid}`;
          let videoEl = document.getElementById(videoId);
          if (!videoEl) {
            videoEl = document.createElement('video');
            videoEl.id = videoId;
            videoEl.className = 'rounded centered';
            videoEl.style.width = '100%';
            videoEl.autoplay = true;
            videoEl.playsInline = true;
            container.appendChild(videoEl);
          }
          if (window.Janus) {
            window.Janus.attachMediaStream(videoEl, stream);
          }
        }
      });
    });

    // Show/hide no video placeholder for remote
    const noVideoContainer = container.querySelector('.no-video-container');
    if (feed.remoteVideos === 0) {
      if (!noVideoContainer) {
        const placeholder = document.createElement('div');
        placeholder.className = 'no-video-container';
        placeholder.innerHTML = `
          <i class="fa-solid fa-video fa-xl no-video-icon"></i>
          <span class="no-video-text">No remote video available</span>
        `;
        container.appendChild(placeholder);
      }
    } else {
      noVideoContainer?.remove();
    }

    // Setup bitrate/resolution display for remote feeds
    if (feed.remoteVideos > 0 && feed.handle && !bitrateIntervalRef.current) {
      const curbitrateId = `curbitrate${feed.rfindex}`;
      const curresId = `curres${feed.rfindex}`;
      
      let bitrateEl = document.getElementById(curbitrateId);
      if (!bitrateEl) {
        bitrateEl = document.createElement('span');
        bitrateEl.id = curbitrateId;
        bitrateEl.className = 'badge bg-info bottom-right m-3';
        container.appendChild(bitrateEl);
      }
      
      let resEl = document.getElementById(curresId);
      if (!resEl) {
        resEl = document.createElement('span');
        resEl.id = curresId;
        resEl.className = 'badge bg-primary bottom-left m-3';
        container.appendChild(resEl);
      }

      bitrateIntervalRef.current = setInterval(() => {
        const videoEl = container.querySelector('video');
        if (!videoEl) return;

        if (feed.handle) {
          const bitrate = feed.handle.getBitrate();
          if (bitrateEl) {
            bitrateEl.textContent = bitrate;
          }
        }

        const width = videoEl.videoWidth;
        const height = videoEl.videoHeight;
        if (width > 0 && height > 0) {
          let res = `${width}x${height}`;
          if (feed.simulcastStarted) {
            res += ' (simulcast)';
          } else if (feed.svcStarted) {
            res += ' (SVC)';
          }
          if (resEl) {
            resEl.textContent = res;
          }
        }
      }, 1000);

      if (setBitrateTimers) {
        setBitrateTimers(prev => ({
          ...prev,
          [feed.rfindex]: bitrateIntervalRef.current
        }));
      }
    }

    return () => {
      if (bitrateIntervalRef.current) {
        clearInterval(bitrateIntervalRef.current);
        bitrateIntervalRef.current = null;
      }
    };
  }, [feed, isLocal, setBitrateTimers]);

  const handleBitrateClick = (value) => {
    if (onBitrateChange) {
      onBitrateChange(value);
    }
  };

  const bitrateOptions = [
    { value: '0', label: 'No limit' },
    { value: '128', label: 'Cap to 128kbit' },
    { value: '256', label: 'Cap to 256kbit' },
    { value: '512', label: 'Cap to 512kbit' },
    { value: '1024', label: 'Cap to 1mbit' },
    { value: '1500', label: 'Cap to 1.5mbit' },
    { value: '2000', label: 'Cap to 2mbit' }
  ];

  const getBitrateLabel = () => {
    const option = bitrateOptions.find(opt => opt.value === bitrate);
    return option ? option.label : 'Bandwidth';
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">
          {title}
          {badge && (
            <span className={`badge ${badgeClass} ms-2`}>{badge}</span>
          )}
          {isLocal && bitrate !== null && (
            <div className="btn-group btn-group-sm top-right">
              <div className="btn-group btn-group-sm">
                <button
                  id="bitrateset"
                  className="btn btn-primary dropdown-toggle"
                  type="button"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  {getBitrateLabel()}
                </button>
                <ul id="bitrate" className="dropdown-menu">
                  {bitrateOptions.map(opt => (
                    <li key={opt.value}>
                      <a
                        className="dropdown-item"
                        href="#"
                        onClick={(e) => {
                          e.preventDefault();
                          handleBitrateClick(opt.value);
                        }}
                      >
                        {opt.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </span>
      </div>
      <div className="card-body" ref={containerRef} id={`video${id}`}>
        {isLocal && localVideos > 0 && (
          <>
            <button
              className="btn btn-warning btn-sm bottom-left m-2"
              id="mute"
              onClick={onToggleMute}
            >
              {isMuted ? 'Unmute' : 'Mute'}
            </button>
            <button
              className="btn btn-warning btn-sm bottom-right m-2"
              id="unpublish"
              onClick={onUnpublish}
            >
              Unpublish
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default VideoCard;
