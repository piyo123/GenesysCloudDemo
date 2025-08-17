const { app } = require('@azure/functions');
const { WebPubSubServiceClient } = require("@azure/web-pubsub");

const AZURE_WEB_PUBSUB_CONNECTION_STRING = process.env.AZURE_WEB_PUBSUB_CONNECTION_STRING || "";
const AZURE_WEB_PUBSUB_HUB_NAME = process.env.AZURE_WEB_PUBSUB_HUB_NAME || "";
const serviceClient = new WebPubSubServiceClient(AZURE_WEB_PUBSUB_CONNECTION_STRING, AZURE_WEB_PUBSUB_HUB_NAME);

app.eventGrid('eventGridTrigger1', {
    handler: async (event, context) => {
        context.log('Kazuma Log: Event grid function processed. event:', event);

        try {
            await serviceClient.sendToAll(event);
            context.log("Kazuma Log: An event was sent to all.");
        } catch (err) {
            context.log('Kazuma Error;', err);
        }
    }
});
