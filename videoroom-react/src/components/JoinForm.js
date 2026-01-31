import React from 'react';

const JoinForm = ({ username, onUsernameChange, onJoin }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      onJoin();
    }
  };

  return (
    <div className="container mt-4" id="videojoin">
      <div className="row">
        <div className="col-md-12" id="controls">
          <div className="input-group mt-3 mb-1" id="registernow">
            <span className="input-group-text">
              <i className="fa-solid fa-user"></i>
            </span>
            <input
              autoComplete="off"
              className="form-control"
              type="text"
              placeholder="Choose a display name"
              id="username"
              value={username}
              onChange={(e) => onUsernameChange(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <span className="input-group-btn">
              <button className="btn btn-success" onClick={onJoin}>
                Join the room
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JoinForm;
