// ref: https://github.com/Azure/azure-webpubsub/blob/main/samples/javascript/chatapp/sdk/server.js

const port = process.env.PORT || 8080

const express = require('express');
const path = require('path');
const { WebPubSubServiceClient } = require('@azure/web-pubsub');
const { WebPubSubEventHandler } = require('@azure/web-pubsub-express');

const app = express();

app.use(express.static('public'));
app.set('view cache', false);
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.get('/', async (req, res) => {
  const prefix = process.env.GENESYS_CLOUD_INTERACTION_DEAIL_PAGE_URL_PREFIX;
  const suffix = process.env.GENESYS_CLOUD_INTERACTION_DEAIL_PAGE_URL_SUFFIX;
  res.render('index', {
    interactionViewPrefix: prefix,
    interactionViewSuffix: suffix
  });
});

const hubName = process.env.AZURE_WEB_PUBSUB_HUBNAME;

let connectionString = process.env.AZURE_WEB_PUBSUB_CONNECTION_STRING || process.argv[2];
console.log(`connection string: ${connectionString}`);
console.log(`hub name: ${hubName}`);
let serviceClient = new WebPubSubServiceClient(connectionString, hubName);
let handler = new WebPubSubEventHandler(hubName, {
  path: '/eventhandler',
  onConnected: async req => {
    console.log("connected");
    await serviceClient.sendToAll({
      type: "system",
      message: `${req.context.userId} joined`
    });
  },
  onDisconnected: async req => {
    // auth the connection and reject the connection if auth failed
    //res.fail(401, "Unauthorized");
    // the following method is also a valid approach
    // res.failWith({ code: 401, detail: "Unauthorized" });
    console.log("disconnected.");
  },
  handleConnect: async (req, res) => {
    console.log("handle connect");
    res.success();
  },
  handleUserEvent: async (req, res) => {
    await serviceClient.sendToAll({
      message: req.data
    });
    console.log("handle user event:");
    console.log(req.data);
    res.success();
  }
});

app.use(handler.getMiddleware());

app.get('/negotiate', async (req, res) => {
  let id = req.query.id;
  if (!id) {
    res.status(400).send('missing user id');
    return;
  }
  let token = await serviceClient.getClientAccessToken({ userId: id });
  res.json({
    url: token.url
  });
});

app.get('/sendTestMessageToAll', async (req, res) => {
  console.log("sending test message to all clients...");
  await serviceClient.sendToAll({
    message: `This is a test message generated at ${new Date().toLocaleString()}`
  });
  res.json({
    message: `Sent a test message to all clients at ${new Date().toLocaleString()}`
  });
});

app.listen(port, () => console.log(`Event handler listening at http://${app.name}:${port}${handler.path}`));