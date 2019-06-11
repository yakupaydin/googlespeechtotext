
from pydub import AudioSegment
import io
import os
import subprocess
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import wave
from google.cloud import storage

filepath = "audiofiles/"
output_filepath = "outputs/"
#ffmpeg -i 175EOldCountryRd.mp4  -ar 16000 -compression_level 10 -c:a flac test34.flac
#sox 175EOldCountryRd.mp4 --rate 16k --bits 16 --channels 1 output.flac
###### export GOOGLE_APPLICATION_CREDENTIALS="/Users/yakupaydin/Desktop/Work/GoogleSpeechToText/credential.json" #####

def mp4_to_wav(audio_file_name):
    cmdline = ['ffmpeg',
           '-i',
           audio_file_name,
           '-ar',
           '16000',
           '-c:a',
           'flac',
           audio_file_name.split('.')[0]+'.flac']
    subprocess.call(cmdline)
def mp3_to_wav(audio_file_name):
    if audio_file_name.split('.')[1] == 'mp3':    
        sound = AudioSegment.from_mp3(audio_file_name)
        audio_file_name = audio_file_name.split('.')[0] + '.wav'
        sound.export(audio_file_name, format="wav")
def frame_rate_channel(audio_file_name):
    with wave.open(audio_file_name, "rb") as wave_file:
        frame_rate = wave_file.getframerate()
        channels = wave_file.getnchannels()
        return frame_rate,channels

def stereo_to_mono(audio_file_name):
    sound = AudioSegment.from_wav(audio_file_name)
    sound = sound.set_channels(1)
    sound.export(audio_file_name, format="wav")


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.delete()
def google_transcribe(audio_file_name):
    
    file_name = filepath + audio_file_name
    mp4_to_wav(file_name)

    # The name of the audio file to transcribe

    
    bucket_name = 'testofspeechtotext'
    source_file_name = filepath + audio_file_name.split('.')[0]+'.flac'
    destination_blob_name = audio_file_name.split('.')[0]+'.flac'
    
    upload_blob(bucket_name, source_file_name, destination_blob_name)
    
    gcs_uri = 'gs://testofspeechtotext/' + audio_file_name.split('.')[0]+'.flac'
    transcript = ''
    
    client = speech.SpeechClient()
    audio = types.RecognitionAudio(uri=gcs_uri)

    config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
    sample_rate_hertz=16000,
    language_code='en-US')

    # Detects speech in the audio file
    operation = client.long_running_recognize(config, audio)
    response = operation.result(timeout=10000)

    for result in response.results:
        transcript += result.alternatives[0].transcript
    
    delete_blob(bucket_name, destination_blob_name)
    return transcript

def write_transcripts(transcript_filename,transcript):
    f= open(output_filepath + transcript_filename,"w+")
    f.write(transcript)
    f.close()

if __name__ == "__main__":
    for audio_file_name in os.listdir(filepath):
        transcript = google_transcribe(audio_file_name)
        transcript_filename = audio_file_name.split('.')[0] + '.txt'
        write_transcripts(transcript_filename,transcript)
