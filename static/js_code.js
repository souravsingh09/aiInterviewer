
//  <script src="https://cdn.jsdelivr.net/npm/microsoft-cognitiveservices-speech-sdk/distrib/browser/microsoft.cognitiveservices.speech.sdk.bundle.js"></script>
// Setting up the azure speech services
const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(subscriptionKey, region);
speechConfig.speechRecognitionLanguage = 'en-US';
speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceResponse_RecognitionTimeout, "60000");
speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceConnection_RecoTimeout, "60000");
speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "60000");
speechConfig.setProperty(SpeechSDK.PropertyId.SpeechSegmentationSilenceTimeoutMs, "120000");

speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceConnection_initialSilenceTimeoutMs, "60000");


const audioConfig = SpeechSDK.AudioConfig.fromDefaultSpeakerOutput();
const audioConfigRecog = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();


// Setting up the azure speech synthesizer and recognizer
const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, 
    // SpeechSDK.RecognitionMode.Interactive, 
    audioConfigRecog
    
);
const synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig, audioConfig);


const conn = SpeechSDK.Connection.fromRecognizer(recognizer);
conn.setMessageProperty("speech.context", "phraseDetection", {
    "INTERACTIVE": {
        "segmentation": {
            "mode": "custom",
            "segmentationSilenceTimeoutMs": 2000
        }
    },
    mode: "Interactive"
});



const startApplication = async () => {
    
        // Speak the response
        await synthesizer.speakTextAsync(
            jsonResp,
            async result => {
                if (result) {
                    console.log(JSON.stringify(result));
                }
                
                if (buttonClick !== true){
                    // Start the recognizer
                    recognizer.startContinuousRecognitionAsync();
                }
            },
            error => {
                console.log(error);
                synthesizer.close();
            }
        );
        
}

recognizer.recognizing = function(s, e) {
    if (sdk.ResultReason.RecognizingSpeech == e.result.reason && e.result.text.length > 0)
    {
        // We don't show sequence numbers for partial results.
        console.log(0, e.result);
    }
    else if (sdk.ResultReason.NoMatch == e.result.reason)
    {
        console.log(0, e.result);
    }
};

recognizer.canceled =(s, e) => {
    if (sdk.CancellationReason.EndOfStream == e.reason)
    {
        console.log(0, e.result);
    }
    else if (sdk.CancellationReason.Error == e.reason)
    {
        console.log(0, e.result);
    }
    else
    {
        console.log(0, e.result);
    }

    recognizer.stopContinuousRecognitionAsync();
};

recognizer.sessionStopped =(s, e) => {
    console.log(0, e.result);
    console.log("inside sessionStopped");

    recognizer.stopContinuousRecognitionAsync();
};


recognizer.recognized = async (s, e) => {
    console.log('Inside recognized');
    const result = e.result;
    if (result.text !== undefined && result.text !== "") {
        // Once the recognizer has recognized the speech, stop the recognizer
        await recognizer.stopContinuousRecognitionAsync(); // Stop recognition after one utterance
        await new Promise(resolve => setTimeout(resolve, 1000));
        

        // Speak the response
        await synthesizer.speakTextAsync(
            jsonResp,
            async result => {
                
                if (buttonClick !== true){
                    // Start the recognizer
                    recognizer.startContinuousRecognitionAsync();
                }
            },
            error => {
                console.log(error);
                synthesizer.close();
            }
        );
    }
};



