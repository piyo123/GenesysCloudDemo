const { EventGridPublisherClient, AzureKeyCredential } = require("@azure/eventgrid");
const { v4: uuidv4 } = require("uuid");

const eventGridTopicEndpoint = process.env["KAZUMA_AZURE_EVENT_GRID_TOPIC_ENDPOINT"] || "";
const eventGridTopicAccessKey = process.env["KAZUMA_AZURE_EVENT_GRID_TOPIC_ACCESS_KEY"] || "";

exports.handler = async (event) => {

    console.log(`RECEIVED EVENT RAW CONTENT\n${JSON.stringify(event)}`);

    const client = new EventGridPublisherClient(
      eventGridTopicEndpoint,
      "CloudEvent", // or EventGrid, Custom
      new AzureKeyCredential(eventGridTopicAccessKey)
    );

    const cloudEvent = {
      id: uuidv4(),
      source: "GenesysCloud.AWSEventBridge",
      type: "genesyscloudevent",
      time: new Date().toISOString(),
      datacontenttype: "application/json",
      data: {
        gcevent: event
      }
    };

    console.log(`SENDING DATA TO AZURE EVENT GRID\n${JSON.stringify(cloudEvent)}`);

    try {

        await client.send([cloudEvent]);
        console.log("event sent successfully.");
        
    } catch (err) {
        console.error("ERROR", err);
    }
  
    const response = {
      statusCode: 200,
      body: JSON.stringify(`${JSON.stringify(event)}`)
    };
    return response;
    
  };
  