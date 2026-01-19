// src/components/DownloadResume.jsx
import React from "react";

const DownloadResume = ({ downloadUrl }) => {
  if (!downloadUrl) return null; // hide button if URL not available

  return (
    <button
      style={{ padding: "10px 20px", marginTop: "20px" }}
      onClick={() => window.open(downloadUrl, "_blank")}
    >
      Download Resume
    </button>
  );
};

export default DownloadResume;
