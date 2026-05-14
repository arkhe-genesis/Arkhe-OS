// substrates/9007_polyglot_mesh/express_adapter.js
const { UniversalAdapter } = require('arkhe-js');
// Mocking app for the snippet context
const app = { use: () => {} };
const temporalChain = {};
const phiMonitor = {};

const adapter = new UniversalAdapter({ temporalChain, phiMonitor });

app.use(async (req, res, next) => {
  const { context, anchor } = await adapter.processRequest(
    req.method, req.path, req.headers, req.body
  );
  req.arkhe = context;

  // Interceptar resposta para ancoragem
  const oldSend = res.send;
  res.send = function (body) {
    adapter.processResponse(context, res.statusCode, body);
    oldSend.call(this, body);
  };
  next();
});
