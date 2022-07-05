from __future__ import division
import re
import sys
import os
import openai
from google.cloud import speech
from time import time,sleep
import pyaudio
from six.moves import queue
from google.cloud import texttospeech
import vlc


# Audio recording parameters
#RATE = 16000
RATE = 32000
CHUNK = int(RATE / 10)  # 100ms


with open('openaiapikey.txt', 'r') as infile:
    open_ai_api_key = infile.read()
openai.api_key = open_ai_api_key


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_memory(content, label):  # label is input or output
    filename = 'memories/%s_%s.txt' % (time(), label)
    with open(filename, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def gpt3_completion(prompt, engine='davinci:ft-david-shapiro:eve-2022-03-25-13-12-25', temp=0.7, top_p=1.0, tokens=250, freq_pen=0.0, pres_pen=0.0, stop=['USER:','RAVEN:']):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                #engine=engine,         # use this for standard models
                model=engine,           # use this for finetune
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            filename = '%s_gpt3.txt' % time()
            with open('gpt3_logs/%s' % filename, 'w') as outfile:
                outfile.write(prompt + '\n\n================\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return None
            print('Error communicating with OpenAI:', oops)
            sleep(1)



class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_loop(responses):
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))
        if not result.is_final:
            a = 0
        else:
            transcript = 'USER: %s' % transcript
            save_memory(transcript, 'input')
            num_chars_printed = 0
            return transcript


def asr_thread():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'raven-344415-9022e591d003.json'
    language_code = "en-US"  # a BCP-47 language tag
    sr_client = speech.SpeechClient()
    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,sample_rate_hertz=RATE,language_code=language_code,)
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
        responses = sr_client.streaming_recognize(streaming_config, requests)
        return(listen_loop(responses))


def tts(tts_client, words, runasync=False):
    print('RAVEN:', words)
    synthesis_input = texttospeech.SynthesisInput(text=words)
    #voice_name = 'en-GB-Wavenet-A' # british female? A, C, D, F
    voice_name = 'en-GB-Wavenet-B' # british male? B, E
    #voice_name = 'en-US-Wavenet-F' # american female? C, E, F, H, G
    #voice_name = 'en-US-Wavenet-D' # american male
    voice = texttospeech.VoiceSelectionParams(name=voice_name, language_code="en-GB")
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=0.95, pitch=-1.5)
    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
    save_memory('RAVEN: %s' % words, 'output')
    player = vlc.MediaPlayer("output.mp3")
    player.play()
    if not runasync:
        sleep(1.5)
        while True:
            state = str(player.get_state())
            if state != 'State.Playing':
                return
            sleep(0.25)


def end_convo(user_speech):
    exit_phrases = ["goodbye", "that's all for now", "i'm done", "exit", "later raven", "bye raven"]
    for i in exit_phrases:
        if i in user_speech.lower():
            return True
    return False


def finetune_response(convo):
    convo_text = ''
    for i in convo:
        convo_text += i + '\n'
    convo_text = convo_text + 'RAVEN:'
    return gpt3_completion(convo_text)


def warmup():
    while True:
        try:
            test = gpt3_completion("USER: RAVEN, are you awake?\nRAVEN:")
            if not test:
                continue
            print("RAVEN is fully online")
            return
        except Exception as oops:
            print(oops)
            sleep(5)


if __name__ == "__main__":
    print('Online!')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'raven-344415-9022e591d003.json'
    tts_client = texttospeech.TextToSpeechClient()
    convo = list()
    greeting = 'I am now fully online. How can I help?'
    farewell = 'Goodbye for now.'
    tts(tts_client, 'Starting up...', True)
    convo.append('RAVEN: Starting up...')
    warmup()
    tts(tts_client, greeting)
    convo.append('RAVEN: %s' % greeting)
    while True:
        user_speech = asr_thread()               # listen until speech
        print(user_speech)                       # print out the words heard
        convo.append(user_speech)                # attach user input to the convo
        if end_convo(user_speech):               # check if user is disengaging
            tts(tts_client, farewell)            # say goodbye
            exit(0)                              # exit program
        response = finetune_response(convo)      # otherwise, generate an output
        convo.append('RAVEN: %s' % response)     # append Raven's response
        tts(tts_client, response)                # say the response
        if len(convo) >= 40:                     # if the convo is getting long
            a = convo.pop(0)                     # remove the oldest messages from the convo