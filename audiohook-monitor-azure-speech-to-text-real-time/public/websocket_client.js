const exit = document.getElementById('exit');
const receiveBox1 = document.getElementById('receive-box1');
const receiveBox2 = document.getElementById('receive-box2');
const appversionArea = document.getElementById('version');
const leftBaloonHtml = '<div class="balloon-chat left"><figure class="icon-img"><img src="operator.png" alt="alt text" ><figcaption class="icon-name">Speaker 1</figcaption></figure><div class="chatting"><p class="chat-text">%s</p></div></div>';
const rightBaloonHtml = '<div class="balloon-chat right"><figure class="icon-img"><img src="customer.png" alt="alt text"><figcaption class="icon-name">Speaker 2</figcaption></figure><div class="chatting"><p class="chat-text">%s</p></div></div></div>';


console.log(window.location.hostname);

if (window.location.hostname == "localhost"){
    connectUri = `ws://localhost:3000/`;
} else {
    connectUri = `wss://${window.location.hostname}/`;
}
const ws = new WebSocket(connectUri);
ws.binaryType = 'arraybuffer';

ws.addEventListener("open", (event) => {
    console.log(`websocket connection opened. Ready State = ${ws.readyState}`);
    receiveBox2.innerHTML += `<span>websocket connection opened. </span>`;
    receiveBox2.innerHTML += `Ready State = ${ws.readyState}</span>`;
});

ws.addEventListener("message", (event) => {

    console.log(`message event received.`);
    //console.log(event.timeStamp);
    //console.log(event.data);

    if (event.data instanceof ArrayBuffer){
        //console.log(event)
        //console.log(event.data);
        //receiveBox1.innerHTML += `<div>${event.data}</div>`;
    } else {

        let jsonObj = JSON.parse(event.data);
        console.log(jsonObj);
        let type = jsonObj.type;

        if (type == "system") {

            receiveBox2.innerHTML += `<p>${jsonObj.message}</p>`;
        
        } else if (type == "transcription") {
            let text = jsonObj.text;
            let speakerId = jsonObj.speakerId;

            if (speakerId.indexOf("1") > 0) {
                receiveBox1.innerHTML += leftBaloonHtml.replace("%s", text);
            } else {
                receiveBox1.innerHTML += rightBaloonHtml.replace("%s", text);
            }

            // auto scroll
            receiveBox1.scrollTop = receiveBox1.scrollHeight;

        } else {
            console.log("unexpected data type.");
        }

    }


 

    // ブラウザで再生するテスト 2024/8/22 16:00 時点で動いてない。
    //if (event.data.constructor !== ArrayBuffer) throw 'expecting ArrayBuffer';
    //playAudioStream(arryBuf);
    // ブラウザで再生するテスト
    
});

ws.addEventListener("close", (event) => {
    console.log("websocket connection closed.");
    receiveBox2.innerHTML += `<span>Disconnected.</span>`;
});

ws.addEventListener("error", (event) => {
    console.log("websocket connection error");
    console.error(event);
    receiveBox2.innerHTML += `<span>websocket connection error</span>`;
});

/*
sendBtn.addEventListener("click", () => {
    ws.send(msgBox.value);
});
*/

exit.addEventListener("click", () => {
    ws.close();
});

/*
Uint8Array.prototype.dumpHex = (zeroX) => {
    var ret = "";

    if (zeroX) {
        var prefix = "0x";
    } else {
        var prefix = "";
    }

    for (i=0;i<this.length;i++){
        var byteOffsetDisp = String(prefix + (('0000' + i.toString(16).toUpperCase()).substring(-4)));
        if (i % 2 == 1) ret += byteOffsetDisp + " ";
        ret += String(prefix + (('0000' + this[i].toString(16).toUpperCase()).substring(-4)));
        if (i % 2 == 0) ret += "\n";
    }

    return ret;
}
*/



//------------------------
// ブラウザで再生するテスト (Web Audio API)　⇒ 2024/8/22 16:00 時点で動いてない。
// https://gist.github.com/ykst/6e80e3566bd6b9d63d19?permalink_comment_id=1798457
// https://qiita.com/alpha_kai_NET/items/7346636d247449e8b342
// https://ics.media/entry/200427/
var ctx = new (window.AudioContext||window.webkitAudioContext);
var initial_delay_sec = 3;
var scheduled_time = 0;

async function playAudioStream(arrayBuffer) {
    var current_time = ctx.currentTime;

    // https://ics.media/entry/200427/ これで正規化できるのかな？ ⇒ だめだ。Failed to execute 'decodeAudioData' on 'BaseAudioContext': Unable to decode audio data
    // https://developer.mozilla.org/ja/docs/Web/API/BaseAudioContext/decodeAudioData
    // この方法は、音声ファイルの断片的なデータではなく、完全なファイルデータに対してのみ動作します。
    //const audio_buf = await ctx.decodeAudioData(arrayBuffer);

    arrayBufferToAudioBuffer(arrayBuffer, ctx)
    .then(audioBuffer => {
        const audio_buf = audioBuffer;
    })

    var audio_src = ctx.createBufferSource();
    audio_src.buffer = audio_buf;
    audio_src.connect(ctx.destination);

    //audio_buf.getChannelData(0).set(audio_f32);

    if (current_time < scheduled_time) {
        playChunk(audio_src, scheduled_time);
        scheduled_time += audio_buf.duration;
    } else {
        playChunk(audio_src, current_time);
        scheduled_time = current_time + audio_buf.duration + initial_delay_sec;
    }
}

function playChunk(audio_src, scheduled_time) {
    if (audio_src.start) {
        audio_src.start(scheduled_time);
    } else {
        audio_src.noteOn(scheduled_time);
    }
}








