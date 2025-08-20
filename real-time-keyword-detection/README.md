# Genesys Cloud Demo
## Real-time Keyword Detection

This solution allows you to detect conversations where a predefined keyword is spoken in real time. It covers all the voice conversations across your entire Genesys Cloud organization. Also, there is no need to open another application window if you implement it through [client application integration](https://help.mypurecloud.com/articles/about-custom-client-application-integrations/).

**Initial implementation: June 2025*

![Architecture](https://gsolar.kazumadachi.com/tools/img/genesyscloudevents_keyword_detection_architecture_with_kigou.png)

**(a) Amazon EventBridge** 
- Receive events via WebSocket from Genesys Notification Service
- Amazon EventBridge Source integration via [AppFoundry](https://help.mypurecloud.com/articles/about-the-amazon-eventbridge-integration/)

**(b) AWS Lambda**
- Triggered by Amazon EventBridge
- Transfer of event data to Azure Event Grid in [CloudEvents 1.0](https://github.com/cloudevents/spec/blob/v1.0/json-format.md) schema

**(c) Azure Event Grid**
- Similar to Amazon EventGrid
- Receive events via HTTP from AWS Lambda

**(d) Azure Function**
- Triggered by Azure Event Grid
- HTTP handshake connection to Azure Web PubSub
- Send event data to Azure Web PubSub via WebSocket

**(e) Azure Web PubSub**
- Fully managed Pub/Sub service for WebSocket-based communication
- Receive Genesys Cloud Events and trigger Web App as event handler

**(f) Azure Web App (Event Handler)**
- Triggered by Azure Web PubSub
- Send events to WebSocket clients

**(g) Static Web App (Client Application)**
- Receive events via WebSocket and render web page content
- Implemented as Genesys Cloud CX client application integration

**Although the architecture may seem somewhat redundant, it was intentionally built on Azure to function independently as a self-contained architecture.*

---
You can see the demonstrations [here](https://gsolar.kazumadachi.com/tools/genesyscloudevents_realtime_keyword_detection_demo_movie.html).

These features listed below are not coverd by this solution at the moment.
- Monitoring of ongoing conversations
- Providing a conversation summary before keyword detection
- Iteractions excluding voice
