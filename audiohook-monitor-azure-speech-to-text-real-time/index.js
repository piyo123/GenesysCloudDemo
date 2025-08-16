const port = process.env.PORT || 3000
const express = require('express');
const app = express();
const WebSocket = require('ws');
const { Buffer } = require('node:buffer');
const WaveFile = require('wavefile').WaveFile;
const NUM_OF_BUF = process.env.NUM_OF_BUF || 1
var audioHookMonitorWS;

app.use(express.static('public'));

app.get("*", (req, res) => {
    res.status(200).send("GET REQUEST SCCEEDED");
});

// main entry point
var server = app.listen(port, () => {
    console.log(`Server listening on port ${server.address().port}. App Version=${process.env.npm_package_version}`);
});

app.use(express.static('public'));

const wss = new WebSocket.Server({ server });

let wav = new WaveFile();

wss.on('connection', (ws, req) => {
    console.log(`new client connected. IP=${req.socket.remoteAddress}. App Version=${process.env.npm_package_version}`);
    console.log(`${req.method} ${req.headers["host"]} HTTP/${req.httpVersion}`);
    console.log(req.headers);

    // Sequence no of server used in messsaging with AudioHookMonitor
    var serverSeq = 1;

    var sumBuf = Buffer.alloc(0);

    if (req.headers["user-agent"] == "GenesysCloud-AudioHook-Client"){
        audioHookMonitorWS = ws;
    }

    ws.on('message', (event, isBinary) => {

        if (isBinary) { // received Audio data
            console.log(`message received on server: isBinary=${isBinary}`);
            
            //console.log(buf); // 3200 bytes per message, sent per 200ms

            if (sumBuf.length == 0) {
                sumBuf = Buffer.from(event);
            } else {
                buf = Buffer.from(event);
                sumBuf = Buffer.concat([sumBuf, buf]);
            }
            
            if (sumBuf.length >= 3200 * NUM_OF_BUF) {
                wav.fromScratch(2, 16000, "8m", sumBuf);
                wav.fromMuLaw(); // Decode 8-bit mu-Law as liner 16-bit PCM: 8bitのままだとAzure Speechが認識しない。
                pushStream.write(wav.toBuffer().buffer.slice());
                
                sumBuf = Buffer.alloc(0);
            }
            
        } else { // received signal data in JSON format

            console.log(`message received on server: ${event}`);

            const reqJson = JSON.parse(event);
            const messageType = reqJson.type;
            const position = reqJson.position;

            console.log(`========================== MESSAGE TYPE=${messageType} ================= POSITION=${position}` );

            var resJsonString;

            switch (messageType) {
                case "open":
                    resJsonString = {
                        version: "2",
                        type: "opened",
                        seq: serverSeq,
                        clientseq: reqJson.seq,
                        id: reqJson.id,
                        parameters: {
                            startPaused: false,
                            media: [
                                {
                                    type: "audio",
                                    format: "PCMU",
                                    channels: ["external", "internal"],
                                    rate: 8000
                                }
                            ]
                        }
                    }
                    break;
                case "update":
                    break;
                case "ping":
                    resJsonString = {
                        version: "2",
                        type: "pong",
                        seq: serverSeq,
                        clientseq: reqJson.seq,
                        id: reqJson.id,
                        parameters: {}
                    }
                    break;
                case "close":
                    resJsonString = {
                        version: "2",
                        type: "closed",
                        seq: serverSeq,
                        clientseq: reqJson.seq,
                        id: reqJson.id,
                        parameters: {}
                    }
                    break;
                case "error":
                    break;
                default:
                    break;
            }

            serverSeq++;
            console.log(`resJsonString = ${JSON.stringify(resJsonString)}`);
            ws.send(JSON.stringify(resJsonString)); // to Audio Hook Monitor

        }

    });

    ws.on('close', (event) => {
        console.log(`disconnected. client id = ${event}`); 
    });

});

// broadcast via WebSocket except Audio Hook Monitor
function broadcast(sendData) {
    wss.clients.forEach((client) => {
        if (client !== audioHookMonitorWS && client.readyState === WebSocket.OPEN) {
            client.send(sendData);
        }
    });
}

//#####################################################################################
// Azure Speech Section
//#####################################################################################

const speechSdk = require("microsoft-cognitiveservices-speech-sdk");
const speechConfig = speechSdk.SpeechConfig.fromSubscription("69017946dd174ae7aa48c740f13b1e0d", "japaneast");
const numOfChannels = 2;
const bitsPerSample = 16;
const samplePerSecond = 8000 * numOfChannels;
const audioFormatTag = 1; //speechSdk.audioFormatTag.PCM; https://learn.microsoft.com/en-us/javascript/api/microsoft-cognitiveservices-speech-sdk/audioformattag?view=azure-node-latest
speechConfig.speechRecognitionLanguage = "ja-JP";
let audioFormat = speechSdk.AudioStreamFormat.getWaveFormat(samplePerSecond, bitsPerSample, numOfChannels, audioFormatTag);
let pushStream = speechSdk.AudioInputStream.createPushStream();
let audioConfig = speechSdk.AudioConfig.fromStreamInput(pushStream, audioFormat);
let conversationTranscriber = new speechSdk.ConversationTranscriber(speechConfig, audioConfig);

conversationTranscriber.sessionStarted = function(s, e) {
    console.log("SessionStarted event");
    console.log(`SessionId:${e.sessionId}`);

    broadcast(`{"type": "system", "message": "SessionStarted event. Session ID=${e.sessionId}"}`);
};

conversationTranscriber.sessionStopped = function(s, e) {
    console.log("SessionStopped event");
    console.log(`SessionId:${e.sessionId}`);

    broadcast(`{"type": "system", "message": "SessionStopped event. Session ID=${e.sessionId}"}`);

    conversationTranscriber.stopTranscribingAsync();
};

conversationTranscriber.canceled = function(s, e) {
    console.log("Canceled event");
    console.log(e.errorDetails);

    broadcast(`{"type": "system", "message": "Canceled event. ${e.errorDetails}"}`);

    conversationTranscriber.stopTranscribingAsync();
};

conversationTranscriber.transcribed = function(s, e) {
    console.log(`TRANSCRIBED: Text=${e.result.text}  Speaker ID=${e.result.speakerId}`);

    broadcast(`{"type": "transcription", "text": "${e.result.text}", "speakerId": "${e.result.speakerId}"}`);
};

// Start conversation transcription
conversationTranscriber.startTranscribingAsync(
    () => {},
    (err) => {
        console.trace(`err - starting transcription: ${err}`);
        broadcast(`"type":"system", "message": "${err}"`);
    }
);
