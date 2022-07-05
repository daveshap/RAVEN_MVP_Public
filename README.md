# RAVEN_MVP_Public

Public MVP of Raven, a general-purpose voice-enabled AI companion

RAVEN = Realtime Assistant Vastly Extensible Network

The MVP is not extensible, it is just a proof of concept. Extensibility is coming. 

## Features

1. Voice-enabled with Google TTS and ASR.
2. Multiple domains and topics. Can serve as tutor, life coach, etc.

## Setup

1. Install VLC in your computer - this is necessary for playing sound
2. Download and deploy FFMPEG, add it to PATH variables: https://ffmpeg.org/download.html and then http://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/
3. Sign up for Google Cloud Services, specifically the TTS and ASR endpoints, generate your credentials JSON file and place it in this directory (see below for more detailed directions)
4. Place your OpenAI API key in a file in this directory called `openaiapikey.txt`
5. Finetune a DAVINCI model in OpenAI with the JSONL file in this directory, **update the MODEL in RAVEN_MVP.py gpt3_completion function**
6. Install pipwin with `pip install pipwin` in an ADMIN prompt
7. Install pyaudio with `pipwin install pyaudio` in the same ADMIN prompt
8. Install REQUIREMENTS.TXT with `pip install -r REQUIREMENTS.txt`

## Google Cloud Services

This part is VERY TEDIOUS, be patient with yourself and set aside an entire day to do it

1. Sign up for Cloud Text to Speech (TTS) here: https://cloud.google.com/text-to-speech 
2. Sign up for Cloud Speech to Text (ASR) here: https://cloud.google.com/speech-to-text 
3. Create your Project in Google Cloud Console: https://console.cloud.google.com/
4. Create the service account for this project as well as the API key (this will ultimately yield a JSON file with the full API key)

I'll probably make a YouTube video just about how to set this up, check back and the link will be **here**

## About the Finetuning Data

The file `raven.jsonl` has over 600 training conversations to teach RAVEN how to behave. These conversations were synthesized over the course of several projects, including a therapeutic/emotional support chatbot and an 
educational/tutor chatbot. In all cases, the conversations were centered around *compassionate listening* and *curiosity about the user*. While it is not explicitly declared in the training data, there are 3 guiding principles (or heuristic imperatives) baked into this training data:

1. Reduce suffering of the user. If RAVEN detects any opportunity to help the user feel better, it will take it.
2. Increase prosperity of the user. To 'prosper' means to 'live well', which RAVEN will support by helping the user to navigate relationships, life, and work.
3. Increase understanding of the user. To understand is to learn, which RAVEN supports by being eager and willing to teach anything.

Later versions of RAVEN will explicitly adhere to these three *core objective functions* (or *heuristic imperatives*) by thinking about them in the background. 