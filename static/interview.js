// This javascript file contains the code for the interview page
// It has the following functionalities
// 1. Setting up the azure speech services for sppech to text and text to speech
// 2. Setting up the Azure open ai service for AI interviewer this incudes asking the backend for the system prompt
// 3. Establishing the web cam to the video element. If the web cam is not on the azure speech service should ask to switch on the web cam and refresh the page
// 4. When the azure speech service is speaking the image with id "ai_interviewer" should have a thich green border
// 5. When the user should speak the video element with id "webcam" should have a thick green border
// 6. Also the transcript of the interview should be maintained and when the interviewee clicks on stop button the transcript should be sent to the backend


// SpeechSDK is imported in the interview_3.html file <script src="https://cdn.jsdelivr.net/npm/microsoft-cognitiveservices-speech-sdk/distrib/browser/microsoft.cognitiveservices.speech.sdk.bundle.js"></script>

// Setting up the azure speech services
let startTime;
let recognitionStarted = false;
let currentUtterance = "";

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


// initialising the buttons
const startInterviewButton = document.getElementById('start_interview');
const stopInterviewButton = document.getElementById('stop_interview');
const popUpDisplay = document.getElementById('popup');

// Creating vaiables for elements in the html
let system_message = document.getElementById('sys_mes');
let system_message_popup = document.getElementById('sys_mes_popup')
const video = document.getElementById('webcam');

// Creating array to store conversation history
let conversation_history = [];

// This function loads the images of the candidate and checks if the face is matching the face in the interview video
async function loadImage() {
    const img = document.createElement('img');
    img.src = imageSrc;

    // Method to run when the image is loaded
    img.onload = async function() {
        const results = await faceapi
            .detectAllFaces(img)
            .withFaceLandmarks()
            .withFaceDescriptors();

        if (!results.length) {
            return;
        }
        
        // Facematcher object which will be used to compare the face in the video with the face in the image
        faceMatcher = new faceapi.FaceMatcher(results);
        console.log(faceMatcher);
        
        // Run the function which extracts the frames from the video and compares the face with the image after every 6 seconds
        setInterval(extractFrames, 6000);
    };
}


// Requesting the system prompt from the Python backend
fetch('/system_prompt', {
    method: 'POST',
})
    .then(response => response.json())
    .then(data => {
        // Process the fetched data here
        conversation_history.push({"role": "system", "content": data['system_prompt']});
        conversation_history.push({"role": "user", "content": "Hello"});
        console.log(conversation_history);
    })
    .catch(error => {
        // Handle any errors that occur during the fetch request
        console.error(error);
    });

// Function to start the interview
const startInterview = () => {
    // Starts the face matching process
    loadImage()
    // Event listener for the start interview button
    startInterviewButton.addEventListener('click', async function() {
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then(stream => {
                const ai_interviewer = document.getElementById('ai_interviewer');
                ai_interviewer.style.display = "block";
                popUpDisplay.style.display = "flex"
                video.srcObject = stream;
                video.width = ai_interviewer.clientWidth;
                video.height = ai_interviewer.clientHeight;

                
            })
            .catch(err => {
                console.log('navigator.getUserMedia error: ', err)
                synthesizer.speakTextAsync(
                    "Please switch on the web cam and refresh the page",
                    result => {
                        system_message.innerText = "Please switch on the web cam and refresh the page";
                        system_message.style.color = "red";

                        console.log(result);
                        synthesizer.close();
                    },
                    error => {
                        console.log(error);
                        synthesizer.close();
                    }
                );
            });

        stopClicked = false;
        startInterviewButton.style.display = 'none';
        stopInterviewButton.style.display = 'none';
        
        // Sending the initial hello message stored in the conversation history to to azure openai service
        let payload = {
            'model':"./models/Meta-Llama-3.1-8B-Instruct-awq",
            // 'model':'casperhansen/llama-3-70b-instruct-awq',
            // 'model':'Llama3',
            'temperature': 0,
            // 'max_tokens': 2000,
            'top_p': 1,
            'messages': conversation_history,
            'stop':"<|eot_id|>"
        }
        let response = await fetch(azure_openai_url,{
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'api-key': azure_openai_key

            },
            body: JSON.stringify(payload)
        })
        
        // Store the response in a variable
        let jsonResp = await response.json();
        console.log(jsonResp['choices'][0]['message']['content']);

        // Add the response to the conversation history
        conversation_history.push(jsonResp['choices'][0]['message'])

        // Speak the response
        await synthesizer.speakTextAsync(
            jsonResp['choices'][0]['message']['content'],
            async result => {
                if (result) {
                    console.log(JSON.stringify(result));
                }
                document.getElementById('ai_interviewer').src = speaking_gif;
                // change the border of the image to green and remove video border
                document.getElementById('webcam').style.border = "none";
                document.getElementById('ai_interviewer').style.border = "thick solid #00FF00";
                // Add a delay before restarting the recognizer
                await new Promise(resolve => setTimeout(resolve, JSON.stringify(result['privAudioDuration'])/10000 - 1000));
                // Remove the green border and add green border to video
                document.getElementById('webcam').style.border = "thick solid #00FF00";
                document.getElementById('ai_interviewer').src = not_speaking_gif;
                document.getElementById('ai_interviewer').style.border = "none";
                if (stopClicked !== true){
                    // Start the recognizer
                    recognizer.startContinuousRecognitionAsync();
                }
            },
            error => {
                console.log(error);
                synthesizer.close();
            }
        );
        
    });
}

// Loads the models from the static folder and once when loaded awaits the start button to start the interview
Promise.all([
    faceapi.nets.ssdMobilenetv1.loadFromUri("../static/models"),
    faceapi.nets.faceLandmark68Net.loadFromUri("../static/models"),
    faceapi.nets.faceRecognitionNet.loadFromUri("../static/models"),
    faceapi.nets.faceExpressionNet.loadFromUri("../static/models"),
    faceapi.nets.ageGenderNet.loadFromUri("../static/models"),
]).then(startInterview);

// Event listener for the stop interview button. ONLY FOR LEGACY PURPOSE NOT USED IN PRESENT IMPLEMENTATION
stopInterviewButton.addEventListener('click', () => {
    stopClicked = true;
    popUpDisplay.style.display = "none"
    recognizer.stopContinuousRecognitionAsync();
    console.log("recognizer_stopped")
    system_message.innerText = "Thank you for attending this interview you interview has been recorded. You can now close the browser."

    // Send the conversation history to the backend
    fetch('/chat_transcript', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(conversation_history)
    })
    .then(response => response.json())
    .then(data => {
        // Process the response from the backend
        console.log(data);
    })
    .catch(error => {
        // Handle any errors that occur during the fetch request
        console.error(error);
    });
});

// Event listener for starting of the recognizer. Used to maintain a variable that is used to extend the default time of maximum recorded speech in azure speech service of 30sec
recognizer.recognizing = function(s, e) {

    if (recognitionStarted === false) {
        startTime = new Date();
        console.log("Start TIME: ",startTime)
        recognitionStarted = true;
    }
    
};


recognizer.recognized = async (s, e) => {
    console.log('Inside recognized');
    const result = e.result;
    // Conditional check which ensures that the result is not empty and that recognition has started
    if (result.text !== undefined && result.text !== "" || ((result.text===undefined || result.text==="") && recognitionStarted===true)) {
        // Once the recognizer has recognized the speech, stop the recognizer
        console.log("TIME DIFFERENCE", Date.now() - startTime)
        // This if condition ensures that speech is recognized for more that 30 seconds. 27000 works well for the condition
        if (Date.now() - startTime < 27000) {
            await recognizer.stopContinuousRecognitionAsync(); // Stop recognition after one utterance
            await new Promise(resolve => setTimeout(resolve, 1000));
            if (result.text !== undefined){
                currentUtterance += result.text;
            }
            console.log(currentUtterance);
            conversation_history.push({"role": "user", "content": currentUtterance})
            console.log(conversation_history);
            let payload = {
                'model':"./models/Meta-Llama-3.1-8B-Instruct-awq",
                // 'model':'casperhansen/llama-3-70b-instruct-awq',
                // 'model':'Llama3',
                'temperature': 0,
                // 'max_tokens': 1000,
                // 'top_p': 1,
                'messages': conversation_history,
                'stop':"<|eot_id|>"
            }
            let response;
            let attempts = 0;
            const maxAttempts = 3; // Maximum number of attempts

            // Retry the request up to 3 times
            while (!response && attempts < maxAttempts) {
            attempts++;
            if (attempts > 1) {
                // sleep or 3 seconds before retry
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
            try {
                console.time("requestTime");
                response = await fetch(azure_openai_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'api-key': azure_openai_key
                },
                body: JSON.stringify(payload)
                });
            } catch (error) {
                console.log(`Attempt ${attempts} failed. Retrying...`);
                if (attempts === maxAttempts) {
                console.log('Max attempts reached. Please check your network connection or the server status.');
                }
            }
            }

            let jsonResp = await response.json();
            console.timeEnd("requestTime");
            console.log(jsonResp);
            console.log(jsonResp['choices'][0]['message']['content']);
            conversation_history.push(jsonResp['choices'][0]['message'])
            // Check whether the response contains the text "Someone will be in touch with you regarding the outcome". if it does then stop the interview
            if (jsonResp['choices'][0]['message']['content'].includes("will be in touch with you regarding the outcome")) {
                stopClicked = true;
                popUpDisplay.style.display = "none"
                system_message.innerText = "Thank you for attending this interview you interview has been recorded. You can now close the browser."
                // Send the conversation history to the backend
                fetch('/chat_transcript', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(conversation_history)
                })
                .then(response => response.json())
                .then(data => {
                    // Process the response from the backend
                    console.log(data);
                })
                .catch(error => {
                    // Handle any errors that occur during the fetch request
                    console.error(error);
                });
            }
            
            // Speak the response
            await synthesizer.speakTextAsync(
                jsonResp['choices'][0]['message']['content'],
                async result => {
                    if (result) {
                        console.log(JSON.stringify(result));
                    }
                    // change the gif to the speaking gif
                    document.getElementById('ai_interviewer').src = speaking_gif;
                    // change the border of the image to green and remove video border
                    document.getElementById('webcam').style.border = "none";
                    document.getElementById('ai_interviewer').style.border = "thick solid #00FF00";
                    // Add a delay before restarting the recognizer
                    await new Promise(resolve => setTimeout(resolve, JSON.stringify(result['privAudioDuration'])/10000 - 1000));
                    // Remove the green border and add green border to video
                    document.getElementById('webcam').style.border = "thick solid #00FF00";
                    document.getElementById('ai_interviewer').src = not_speaking_gif;
                    document.getElementById('ai_interviewer').style.border = "none";
                    if (stopClicked !== true){
                        // Start the recognizer
                        recognitionStarted = false;
                        currentUtterance = "";
                        recognizer.startContinuousRecognitionAsync();
                        
                    }
                },
                error => {
                    console.log(error);
                    synthesizer.close();
                }
            );
        } else {
            console.log("User spoke for more than 30 seconds");
            currentUtterance += result.text;
            startTime = Date.now();

        }
    } 
};

async function extractFrames() {
    const displaySize = { width: video.videoWidth, height: video.videoHeight };

    const results = await faceapi
        .detectAllFaces(video)
        .withFaceLandmarks()
        .withFaceDescriptors();

    if (results.length > 1){
        system_message_popup.innerText = "Multiple people in the frame";
        system_message_popup.style.color = "red"; // Replace 'red' with the color you want
        console.log("Multiple people in the frame");

    }else if (results.length > 0) {
        // const canvas = faceapi.createCanvasFromMedia(video);
        // faceapi.matchDimensions(canvas, displaySize);

        results.forEach((result) => {
            const bestMatch = faceMatcher.findBestMatch(result.descriptor);
            // console.log(bestMatch.toString());

            // Check whether the best match is equal to person 1
            // First we have to extract only the name from the string
            const name = bestMatch.toString().split(" ")[0];
            if (name !== "person") {
                // access tag with id "interview_status" and change the innerHTML to "Candidate face mismatch"
                system_message_popup.innerText = "Candidate face mismatch. Always face the camera.";
                system_message_popup.style.color = "red"; // Replace 'red' with the color you want
                console.log(name);
            } else {
                system_message_popup.innerText = "Candidate face is matching";
                system_message_popup.style.color = "green"; // Replace 'red' with the color you want
            }

        });

    } else {
        system_message_popup.innerText = "No face detected in the frame";
        system_message_popup.style.color = "red"; // Replace 'red' with the color you want

    }
}

