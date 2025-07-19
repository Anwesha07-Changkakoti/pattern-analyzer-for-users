let deviceId = localStorage.getItem("deviceId");
if (!deviceId) {
  deviceId = crypto.randomUUID(); // generates a unique ID
  localStorage.setItem("deviceId", deviceId);
}
export default deviceId;
