import { useEffect, useState } from "react";
import socket from "../utils/socket";

export default function LiveNetworkStats({ userId }) {
  const [upload, setUpload] = useState(0);
  const [download, setDownload] = useState(0);

  useEffect(() => {
    socket.on("network_stats", (data) => {
      if (data.user_id === userId) {
        setUpload(data.upload_kb);
        setDownload(data.download_kb);
      }
    });
    return () => {
      socket.off("network_stats");
    };
  }, [userId]);

  return (
    <div className="text-green-400 p-2">
      <div>📤 Upload: {upload.toFixed(2)} KB</div>
      <div>📥 Download: {download.toFixed(2)} KB</div>
    </div>
  );
}
