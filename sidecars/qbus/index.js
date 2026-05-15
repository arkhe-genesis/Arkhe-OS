const express = require('express');
const app = express();
const port = 8080;

app.get('/health', (req, res) => {
  res.send('Q-Bus Sidecar is running');
});

app.listen(port, () => {
  console.log(`Q-Bus Sidecar listening at http://localhost:${port}`);
});
