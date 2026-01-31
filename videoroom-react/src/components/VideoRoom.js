import React, { useState, useEffect, useRef, useCallback } from 'react';
import { server, iceServers, iceTransportPolicy } from '../settings';
import VideoCard from './VideoCard';
import JoinForm from './JoinForm';
import './VideoRoom.css';

const VideoRoom = () => {
  const [started, setStarted] = useState(false);
  const [joined, setJoined] = useState(false);
  const [showDetails, setShowDetails] = useState(true);
  const [showJoinForm, setShowJoinForm] = useState(false);
  const [showVideos, setShowVideos] = useState(false);
  const [username, setUsername] = useState('');
  const [myId, setMyId] = useState(null);
  const [myPvtId, setMyPvtId] = useState(null);
  const [myUsername, setMyUsername] = useState(null);
  const [localTracks, setLocalTracks] = useState({});
  const [localVideos, setLocalVideos] = useState(0);
  const [feeds, setFeeds] = useState([null, null, null, null, null, null]);
  const [feedStreams, setFeedStreams] = useState({});
  const [bitrateTimers, setBitrateTimers] = useState({});
  const [publisher, setPublisher] = useState(null);
  const [myStream, setMyStream] = useState(null);
  const [bitrate, setBitrate] = useState(null);
  const [isMuted, setIsMuted] = useState(false);

  const janusRef = useRef(null);
  const sfutestRef = useRef(null);
  const opaqueIdRef = useRef(`videoroomtest-${window.Janus?.randomString(12) || 'test'}`);
  const myroomRef = useRef(1234);
  const myPvtIdRef = useRef(null);

  // Parse query string
  const getQueryStringValue = (name) => {
    name = name.replace(/[[]/, "\\[").replace(/[\]]/, "\\]");
    const regex = new RegExp("[\\?&]" + name + "=([^&#]*)");
    const results = regex.exec(window.location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
  };

  // Get query parameters
  const doSimulcast = getQueryStringValue("simulcast") === "yes" || getQueryStringValue("simulcast") === "true";
  const doSvc = getQueryStringValue("svc") || null;
  const acodec = getQueryStringValue("acodec") || null;
  const vcodec = getQueryStringValue("vcodec") || null;
  const doDtx = getQueryStringValue("dtx") === "yes" || getQueryStringValue("dtx") === "true";
  const subscriberMode = getQueryStringValue("subscriber-mode") === "yes" || getQueryStringValue("subscriber-mode") === "true";
  const useMsid = getQueryStringValue("msid") === "yes" || getQueryStringValue("msid") === "true";

  // Escape XML tags
  const escapeXmlTags = (value) => {
    if (value) {
      let escapedValue = value.replace(/</g, '&lt');
      escapedValue = escapedValue.replace(/>/g, '&gt');
      return escapedValue;
    }
    return value;
  };

  // Safe bootbox alert with fallback
  const safeAlert = (message, callback) => {
    try {
      if (window.bootbox && typeof window.bootbox.alert === 'function') {
        if (callback) {
          window.bootbox.alert(message, callback);
        } else {
          window.bootbox.alert(message);
        }
      } else if (window.toastr && typeof window.toastr.error === 'function') {
        window.toastr.error(message);
        if (callback) setTimeout(callback, 100);
      } else {
        alert(message);
        if (callback) setTimeout(callback, 100);
      }
    } catch (e) {
      console.error('Error showing alert:', e);
      alert(message);
      if (callback) setTimeout(callback, 100);
    }
  };

  // Initialize Janus
  useEffect(() => {
    if (!window.Janus) return;

    const roomParam = getQueryStringValue("room");
    if (roomParam !== "") {
      myroomRef.current = parseInt(roomParam);
    }

    window.Janus.init({
      debug: "all",
      callback: () => {
        console.log("Janus initialized");
      }
    });
  }, []);

  // Handle start button
  const handleStart = () => {
      if (!window.Janus) {
      safeAlert("Janus library not loaded");
      return;
    }

    if (!window.Janus.isWebrtcSupported()) {
      safeAlert("No WebRTC support... ");
      return;
    }

    setStarted(true);

    // Create Janus session
    const janus = new window.Janus({
      server: server,
      iceServers: iceServers,
      success: () => {
        // Attach to VideoRoom plugin
        janus.attach({
          plugin: "janus.plugin.videoroom",
          opaqueId: opaqueIdRef.current,
          success: (pluginHandle) => {
            sfutestRef.current = pluginHandle;
            janusRef.current = janus;
            setShowDetails(false);
            setShowJoinForm(true);
            window.Janus.log("Plugin attached! (" + pluginHandle.getPlugin() + ", id=" + pluginHandle.getId() + ")");
          },
          error: (error) => {
            window.Janus.error("  -- Error attaching plugin...", error);
            safeAlert("Error attaching plugin... " + error);
            setStarted(false);
          },
          consentDialog: (on) => {
            window.Janus.debug("Consent dialog should be " + (on ? "on" : "off") + " now");
            // Handle consent dialog if needed
          },
          iceState: (state) => {
            window.Janus.log("ICE state changed to " + state);
          },
          mediaState: (medium, on, mid) => {
            window.Janus.log("Janus " + (on ? "started" : "stopped") + " receiving our " + medium + " (mid=" + mid + ")");
          },
          webrtcState: (on) => {
            window.Janus.log("Janus says our WebRTC PeerConnection is " + (on ? "up" : "down") + " now");
            if (!on) return;
            setPublisher(true);
            setBitrate(0);
          },
          slowLink: (uplink, lost, mid) => {
            window.Janus.warn("Janus reports problems " + (uplink ? "sending" : "receiving") +
              " packets on mid " + mid + " (" + lost + " lost packets)");
          },
          onmessage: (msg, jsep) => {
            window.Janus.debug(" ::: Got a message (publisher) :::", msg);
            const event = msg["videoroom"];
            window.Janus.debug("Event: " + event);
            
            if (event) {
              if (event === "joined") {
                const privateId = msg["private_id"];
                setMyId(msg["id"]);
                setMyPvtId(privateId);
                myPvtIdRef.current = privateId;
                window.Janus.log("Successfully joined room " + msg["room"] + " with ID " + msg["id"]);
                
                setJoined(true);
              if (subscriberMode) {
                  setShowJoinForm(false);
                  setShowVideos(true);
                } else {
                  publishOwnFeed(true);
                }
                
                if (msg["publishers"]) {
                  const list = msg["publishers"];
                  window.Janus.debug("Got a list of available publishers/feeds:", list);
                  for (let f in list) {
                    if (list[f]["dummy"]) continue;
                    const id = list[f]["id"];
                    const streams = list[f]["streams"];
                    const display = list[f]["display"];
                    const streamList = streams.map(stream => ({
                      ...stream,
                      id: id,
                      display: display
                    }));
                    setFeedStreams(prev => ({ ...prev, [id]: streamList }));
                    window.Janus.debug("  >> [" + id + "] " + display + ":", streams);
                    newRemoteFeed(id, display, streamList, privateId);
                  }
                }
              } else if (event === "destroyed") {
                window.Janus.warn("The room has been destroyed!");
                safeAlert("The room has been destroyed", () => {
                  window.location.reload();
                });
              } else if (event === "event") {
                if (msg["streams"]) {
                  const streams = msg["streams"];
                  const streamList = streams.map(stream => ({
                    ...stream,
                    id: myId,
                    display: myUsername
                  }));
                  setFeedStreams(prev => ({ ...prev, [myId]: streamList }));
                } else if (msg["publishers"]) {
                  const list = msg["publishers"];
                  window.Janus.debug("Got a list of available publishers/feeds:", list);
                  for (let f in list) {
                    if (list[f]["dummy"]) continue;
                    const id = list[f]["id"];
                    const display = list[f]["display"];
                    const streams = list[f]["streams"];
                    const streamList = streams.map(stream => ({
                      ...stream,
                      id: id,
                      display: display
                    }));
                    setFeedStreams(prev => ({ ...prev, [id]: streamList }));
                    window.Janus.debug("  >> [" + id + "] " + display + ":", streams);
                    newRemoteFeed(id, display, streamList, myPvtIdRef.current);
                  }
                } else if (msg["leaving"]) {
                  const leaving = msg["leaving"];
                  window.Janus.log("Publisher left: " + leaving);
                  removeRemoteFeed(leaving);
                } else if (msg["unpublished"]) {
                  const unpublished = msg["unpublished"];
                  window.Janus.log("Publisher left: " + unpublished);
                  if (unpublished === 'ok') {
                    sfutestRef.current?.hangup();
                    return;
                  }
                  removeRemoteFeed(unpublished);
                } else if (msg["error"]) {
                  if (msg["error_code"] === 426) {
                    safeAlert(
                      "Apparently room " + myroomRef.current + " (the one this demo uses as a test room) " +
                      "does not exist. Do you have an updated janus.plugin.videoroom.jcfg " +
                      "configuration file? If not, make sure you copy the details of room " + myroomRef.current + " " +
                      "from that sample in your current configuration file, then restart Janus and try again."
                    );
                  } else {
                    safeAlert(msg["error"]);
                  }
                }
              }
            }
            
            if (jsep) {
              window.Janus.debug("Handling SDP as well...", jsep);
              sfutestRef.current?.handleRemoteJsep({ jsep: jsep });
              
              const audio = msg["audio_codec"];
              if (myStream && myStream.getAudioTracks() && myStream.getAudioTracks().length > 0 && !audio) {
                window.toastr?.warning("Our audio stream has been rejected, viewers won't hear us");
              }
              const video = msg["video_codec"];
              if (myStream && myStream.getVideoTracks() && myStream.getVideoTracks().length > 0 && !video) {
                window.toastr?.warning("Our video stream has been rejected, viewers won't see us");
              }
            }
          },
          onlocaltrack: (track, on) => {
            window.Janus.debug("Local track " + (on ? "added" : "removed") + ":", track);
            const trackId = track.id.replace(/[{}]/g, "");
            
            if (!on) {
              const stream = localTracks[trackId];
              if (stream) {
                try {
                  const tracks = stream.getTracks();
                  for (let i in tracks) {
                    const mst = tracks[i];
                    if (mst !== null && mst !== undefined) mst.stop();
                  }
                } catch (e) {}
              }
              
              if (track.kind === "video") {
                setLocalVideos(prev => prev - 1);
              }
              
              setLocalTracks(prev => {
                const newTracks = { ...prev };
                delete newTracks[trackId];
                return newTracks;
              });
              return;
            }
            
            if (localTracks[trackId]) {
              return;
            }
            
            setShowVideos(true);
            
            if (track.kind === "audio") {
              if (localVideos === 0) {
                // No video placeholder handled in VideoCard
              }
            } else {
              setLocalVideos(prev => prev + 1);
              const stream = new MediaStream([track]);
              setLocalTracks(prev => ({ ...prev, [trackId]: stream }));
              window.Janus.log("Created local stream:", stream);
            }
          },
          onremotetrack: () => {
            // Publisher stream is sendonly
          },
          oncleanup: () => {
            window.Janus.log(" ::: Got a cleanup notification: we are unpublished now :::");
            setMyStream(null);
            setFeedStreams(prev => {
              const newStreams = { ...prev };
              delete newStreams[myId];
              return newStreams;
            });
            setPublisher(false);
            setBitrate(null);
            setLocalTracks({});
            setLocalVideos(0);
          }
        });
      },
      error: (error) => {
        window.Janus.error(error);
        safeAlert(error, () => {
          window.location.reload();
        });
        setStarted(false);
      },
      destroyed: () => {
        window.location.reload();
      }
    });
  };

  // Publish own feed
  const publishOwnFeed = (useAudio) => {
    if (!sfutestRef.current) return;

    const tracks = [];
    if (useAudio) {
      tracks.push({ type: 'audio', capture: true, recv: false });
    }
    tracks.push({
      type: 'video',
      capture: true,
      recv: false,
      simulcast: doSimulcast,
      svc: ((vcodec === 'vp9' || vcodec === 'av1') && doSvc) ? doSvc : null
    });

    sfutestRef.current.createOffer({
      tracks: tracks,
      customizeSdp: (jsep) => {
        if (doDtx) {
          jsep.sdp = jsep.sdp.replace("useinbandfec=1", "useinbandfec=1;usedtx=1");
        }
      },
      success: (jsep) => {
        window.Janus.debug("Got publisher SDP!", jsep);
        const publish = { request: "configure", audio: useAudio, video: true };
        if (acodec) publish["audiocodec"] = acodec;
        if (vcodec) publish["videocodec"] = vcodec;
        sfutestRef.current?.send({ message: publish, jsep: jsep });
      },
      error: (error) => {
        window.Janus.error("WebRTC error:", error);
        if (useAudio) {
          publishOwnFeed(false);
        } else {
          safeAlert("WebRTC error... " + error.message);
        }
      }
    });
  };

  // Register username
  const handleRegister = () => {
    if (!username || username === "") {
      window.toastr?.warning("Insert your display name (e.g., pippo)");
      return;
    }
    if (/[^a-zA-Z0-9]/.test(username)) {
      window.toastr?.warning('Input is not alphanumeric');
      setUsername("");
      return;
    }

    const register = {
      request: "join",
      room: myroomRef.current,
      ptype: "publisher",
      display: username
    };
    const escapedUsername = escapeXmlTags(username);
    setMyUsername(escapedUsername);
    sfutestRef.current?.send({ message: register });
  };

  // New remote feed
  const newRemoteFeed = (id, display, streams, privateId = null) => {
    if (!janusRef.current) return;

    const remoteFeed = {
      rfid: id,
      rfdisplay: escapeXmlTags(display),
      rfindex: null,
      remoteTracks: {},
      remoteVideos: 0,
      simulcastStarted: false,
      svcStarted: false
    };

    janusRef.current.attach({
      plugin: "janus.plugin.videoroom",
      opaqueId: opaqueIdRef.current,
      success: (pluginHandle) => {
        remoteFeed.handle = pluginHandle;
        window.Janus.log("Plugin attached! (" + pluginHandle.getPlugin() + ", id=" + pluginHandle.getId() + ")");
        window.Janus.log("  -- This is a subscriber");

        const subscription = [];
        for (let i in streams) {
          const stream = streams[i];
          if (stream.type === "video" && window.Janus.webRTCAdapter.browserDetails.browser === "safari" &&
              ((stream.codec === "vp9" && !window.Janus.safariVp9) || (stream.codec === "vp8" && !window.Janus.safariVp8))) {
            window.toastr?.warning("Publisher is using " + stream.codec.toUpperCase +
              ", but Safari doesn't support it: disabling video stream #" + stream.mindex);
            continue;
          }
          subscription.push({
            feed: stream.id,
            mid: stream.mid
          });
        }

        const subscribe = {
          request: "join",
          room: myroomRef.current,
          ptype: "subscriber",
          streams: subscription,
          use_msid: useMsid
        };
        // Only add private_id if it's set (positive integer)
        const pvtId = privateId !== null && privateId !== undefined ? privateId : myPvtIdRef.current;
        if (pvtId !== null && pvtId !== undefined && Number.isInteger(pvtId) && pvtId > 0) {
          subscribe.private_id = pvtId;
        }
        pluginHandle.send({ message: subscribe });
      },
      error: (error) => {
        window.Janus.error("  -- Error attaching plugin...", error);
        safeAlert("Error attaching plugin... " + error);
      },
      iceState: (state) => {
        window.Janus.log("ICE state (feed #" + remoteFeed.rfindex + ") changed to " + state);
      },
      webrtcState: (on) => {
        window.Janus.log("Janus says this WebRTC PeerConnection (feed #" + remoteFeed.rfindex + ") is " + (on ? "up" : "down") + " now");
      },
      slowLink: (uplink, lost, mid) => {
        window.Janus.warn("Janus reports problems " + (uplink ? "sending" : "receiving") +
          " packets on mid " + mid + " (" + lost + " lost packets)");
      },
          onmessage: (msg, jsep) => {
            window.Janus.debug(" ::: Got a message (subscriber) :::", msg);
            const event = msg["videoroom"];
            window.Janus.debug("Event: " + event);
            
            if (msg["error"]) {
              safeAlert(msg["error"]);
            } else if (event) {
              if (event === "attached") {
                let assignedIndex = null;
                setFeeds(prev => {
                  const newFeeds = [...prev];
                  for (let i = 1; i < 6; i++) {
                    if (!newFeeds[i]) {
                      remoteFeed.rfindex = i;
                      assignedIndex = i;
                      newFeeds[i] = remoteFeed;
                      break;
                    }
                  }
                  return newFeeds;
                });
                if (assignedIndex) {
                  window.Janus.log("Successfully attached to feed in room " + msg["room"]);
                }
              } else if (event === "event") {
                const substream = msg["substream"];
                const temporal = msg["temporal"];
                if ((substream !== null && substream !== undefined) || (temporal !== null && temporal !== undefined)) {
                  if (!remoteFeed.simulcastStarted) {
                    remoteFeed.simulcastStarted = true;
                    setFeeds(prev => {
                      const newFeeds = [...prev];
                      if (newFeeds[remoteFeed.rfindex]) {
                        newFeeds[remoteFeed.rfindex] = { ...newFeeds[remoteFeed.rfindex], simulcastStarted: true };
                      }
                      return newFeeds;
                    });
                  }
                }
                const spatial = msg["spatial_layer"];
                const temporal2 = msg["temporal_layer"];
                if ((spatial !== null && spatial !== undefined) || (temporal2 !== null && temporal2 !== undefined)) {
                  if (!remoteFeed.svcStarted) {
                    remoteFeed.svcStarted = true;
                    setFeeds(prev => {
                      const newFeeds = [...prev];
                      if (newFeeds[remoteFeed.rfindex]) {
                        newFeeds[remoteFeed.rfindex] = { ...newFeeds[remoteFeed.rfindex], svcStarted: true };
                      }
                      return newFeeds;
                    });
                  }
                }
              }
            }
            
            if (jsep) {
              window.Janus.debug("Handling SDP as well...", jsep);
              const stereo = (jsep.sdp.indexOf("stereo=1") !== -1);
              remoteFeed.handle.createAnswer({
                jsep: jsep,
                tracks: [{ type: 'data' }],
                customizeSdp: (jsep) => {
                  if (stereo && jsep.sdp.indexOf("stereo=1") == -1) {
                    jsep.sdp = jsep.sdp.replace("useinbandfec=1", "useinbandfec=1;stereo=1");
                  }
                },
                success: (jsep) => {
                  window.Janus.debug("Got SDP!", jsep);
                  const body = { request: "start", room: myroomRef.current };
                  remoteFeed.handle.send({ message: body, jsep: jsep });
                },
                error: (error) => {
                  window.Janus.error("WebRTC error:", error);
                  safeAlert("WebRTC error... " + error.message);
                }
              });
            }
          },
      onlocaltrack: () => {
        // Subscriber stream is recvonly
      },
          onremotetrack: (track, mid, on, metadata) => {
            window.Janus.debug(
              "Remote feed #" + remoteFeed.rfindex +
              ", remote track (mid=" + mid + ") " +
              (on ? "added" : "removed") +
              (metadata ? " (" + metadata.reason + ") " : "") + ":", track
            );
            
            if (!on) {
              if (track.kind === "video") {
                remoteFeed.remoteVideos = Math.max(0, remoteFeed.remoteVideos - 1);
              }
              delete remoteFeed.remoteTracks[mid];
              setFeeds(prev => {
                const newFeeds = [...prev];
                const index = remoteFeed.rfindex;
                if (newFeeds[index]) {
                  newFeeds[index] = { ...newFeeds[index], remoteTracks: { ...remoteFeed.remoteTracks }, remoteVideos: remoteFeed.remoteVideos };
                }
                return newFeeds;
              });
              return;
            }
            
            if (track.kind === "audio") {
              const stream = new MediaStream([track]);
              remoteFeed.remoteTracks[mid] = stream;
              window.Janus.log("Created remote audio stream:", stream);
            } else {
              remoteFeed.remoteVideos++;
              const stream = new MediaStream([track]);
              remoteFeed.remoteTracks[mid] = stream;
              window.Janus.log("Created remote video stream:", stream);
            }
            
            setFeeds(prev => {
              const newFeeds = [...prev];
              const index = remoteFeed.rfindex;
              if (newFeeds[index]) {
                newFeeds[index] = { ...newFeeds[index], remoteTracks: { ...remoteFeed.remoteTracks }, remoteVideos: remoteFeed.remoteVideos };
              }
              return newFeeds;
            });
          },
      oncleanup: () => {
        window.Janus.log(" ::: Got a cleanup notification (remote feed " + id + ") :::");
        if (bitrateTimers[remoteFeed.rfindex]) {
          clearInterval(bitrateTimers[remoteFeed.rfindex]);
          setBitrateTimers(prev => {
            const newTimers = { ...prev };
            delete newTimers[remoteFeed.rfindex];
            return newTimers;
          });
        }
        remoteFeed.remoteTracks = {};
        remoteFeed.remoteVideos = 0;
      }
    });
  };

  // Remove remote feed
  const removeRemoteFeed = (id) => {
    setFeeds(prev => {
      const newFeeds = [...prev];
      for (let i = 1; i < 6; i++) {
        if (newFeeds[i] && newFeeds[i].rfid === id) {
          newFeeds[i].handle?.detach();
          newFeeds[i] = null;
          break;
        }
      }
      return newFeeds;
    });
    setFeedStreams(prev => {
      const newStreams = { ...prev };
      delete newStreams[id];
      return newStreams;
    });
  };

  // Handle stop
  const handleStop = () => {
    if (janusRef.current) {
      janusRef.current.destroy();
    }
    setStarted(false);
    setJoined(false);
    setShowDetails(true);
    setShowJoinForm(false);
    setShowVideos(false);
  };

  // Handle bitrate change
  const handleBitrateChange = (bitrateValue) => {
    if (!sfutestRef.current) return;
    const bitrateKbps = parseInt(bitrateValue) * 1000;
    if (bitrateKbps === 0) {
      window.Janus.log("Not limiting bandwidth via REMB");
    } else {
      window.Janus.log("Capping bandwidth to " + bitrateKbps + " via REMB");
    }
    setBitrate(bitrateValue);
    sfutestRef.current.send({ message: { request: "configure", bitrate: bitrateKbps } });
  };

  // Toggle mute
  const handleToggleMute = () => {
    if (!sfutestRef.current) return;
    const muted = sfutestRef.current.isAudioMuted();
    if (muted) {
      sfutestRef.current.unmuteAudio();
      setIsMuted(false);
    } else {
      sfutestRef.current.muteAudio();
      setIsMuted(true);
    }
  };

  // Unpublish
  const handleUnpublish = () => {
    if (!sfutestRef.current) return;
    sfutestRef.current.send({ message: { request: "unpublish" } });
  };

  return (
    <div className="container">
      <div className="row">
        <div className="col-md-12">
          <div className="pb-2 mt-4 mb-2 border-bottom">
            <h1>
              Plugin Demo: Video Room
              {!started && (
                <button className="btn btn-secondary ms-2" onClick={handleStart}>
                  Start
                </button>
              )}
              {started && (
                <button className="btn btn-secondary ms-2" onClick={handleStop}>
                  Stop
                </button>
              )}
            </h1>
          </div>

          {showDetails && (
            <div className="container" id="details">
              <div className="row">
                <div className="alert alert-primary mt-2 mb-5">
                  Want to learn more about the <strong>VideoRoom</strong> plugin?
                  Check the <a target="_blank" rel="noopener noreferrer" href="https://janus.conf.meetecho.com/docs/videoroom">Documentation</a>.
                </div>
              </div>
              <div className="row">
                <div className="col-md-12">
                  <h3>Demo details</h3>
                  <p>This demo is an example of how you can use the Video Room plugin to
                  implement a simple videoconferencing application. In particular, this
                  demo page allows you to have up to 6 active participants at the same time:
                  more participants joining the room will be instead just passive users.
                  No mixing is involved: all media are just relayed in a publisher/subscriber
                  approach. This means that the plugin acts as a SFU (Selective Forwarding Unit)
                  rather than an MCU (Multipoint Control Unit).</p>
                  <div className="alert alert-info">Notice that this is the <b>original</b> VideoRoom
                  demo, and uses a different PeerConnections per each subscription: if
                  you want to test the new multistream support, instead, try the
                  <a href="mvideoroom.html">multistream VideoRoom demo</a>
                  instead. The two demos are interoperable, if you want to see how
                  different subscription mechanisms are used on the same sources.</div>
                  <p>If you're interested in testing how simulcasting or SVC can be used within
                  the context of a videoconferencing application, just pass a
                  <code>?simulcast=true</code> (for simulcast) or <code>?svc=&lt;mode&gt;</code>
                  (for SVC) query string to the url of this page and reload it. Notice that
                  simulcast will only work when using VP8 or H.264 (or, if you're using a
                  recent version of Chrome, VP9 and AV1 too), while SVC will only work
                  if you're using VP9 or AV1 on a browser that supports setting the <code>scalabilityMode</code>.
                  Besides, notice that simulcasting/SVC will only be sent if the browser thinks
                  there is enough bandwidth, so you may have to play with the Bandwidth selector to
                  increase it. New buttons to play with the feature will automatically
                  appear for viewers when receiving any simulcast/SVC stream. Notice that
                  no simulcast/SVC support is needed for watching, only for publishing.</p>
                  <p>To use the demo, just insert a username to join the default room that
                  is configured. This will add you to the list of participants, and allow
                  you to automatically send your audio/video frames and receive the other
                  participants' feeds. The other participants will appear in separate
                  panels, whose title will be the names they chose when registering at
                  the demo.</p>
                  <p>Press the <code>Start</code> button above to launch the demo.</p>
                </div>
              </div>
            </div>
          )}

          {showJoinForm && (
            <div className="container mt-4" id="videojoin">
              <div className="row">
                <span className="badge bg-info" id="you">{myUsername || 'Not joined'}</span>
                <div className="col-md-12" id="controls">
                  <div className="input-group mt-3 mb-1" id="registernow">
                    <span className="input-group-text"><i className="fa-solid fa-user"></i></span>
                    <input
                      autoComplete="off"
                      className="form-control"
                      type="text"
                      placeholder="Choose a display name"
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleRegister();
                        }
                      }}
                    />
                    <span className="input-group-btn">
                      <button className="btn btn-success" onClick={handleRegister}>
                        Join the room
                      </button>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {showVideos && (
            <div className="container mt-4" id="videos">
              <div className="row">
                <div className="col-md-4">
                  <VideoCard
                    title="Local Video"
                    badge={publisher ? "Publisher" : null}
                    badgeClass="bg-primary"
                    id="local"
                    localTracks={localTracks}
                    localVideos={localVideos}
                    bitrate={bitrate}
                    onBitrateChange={handleBitrateChange}
                    onToggleMute={handleToggleMute}
                    onUnpublish={handleUnpublish}
                    sfutest={sfutestRef.current}
                    isMuted={isMuted}
                  />
                </div>
                {[1, 2, 3, 4, 5].map((index) => (
                  <div key={index} className="col-md-4">
                    <VideoCard
                      title={`Remote Video #${index}`}
                      badge={feeds[index] ? feeds[index].rfdisplay : null}
                      badgeClass="bg-info"
                      id={`remote${index}`}
                      feed={feeds[index]}
                      bitrateTimers={bitrateTimers}
                      setBitrateTimers={setBitrateTimers}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoRoom;
