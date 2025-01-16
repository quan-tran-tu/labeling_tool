import glob
import os
import whisper
from base import MetadataBuffer, AUDIO_DIR, Gender, LanguageAccent, Metadata

class WhisperBuffer(MetadataBuffer):
    model = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MetadataBuffer, cls).__new__(cls)
            cls._instance._init_storage()
            cls._instance._init_whisper()
        return cls._instance
    
    def _init_whisper(self):
        model_name = "turbo"
        self.model = whisper.load_model(model_name, device="cuda")

buffer = WhisperBuffer()
def update_transcript(metadata: Metadata):
    summary = metadata.get_summary()
    buffer.add_item(summary)

audio_files = glob.glob(os.path.join(AUDIO_DIR, "*.wav"))
for audio_file in audio_files:
    if audio_file in buffer.processed_files:
        continue
    # Normalize the audio file here
    # Transcribe the audio file
    result = buffer.model.transcribe(audio_file, language="en", task="transcribe")

    transcript = result['text']
    metadata = Metadata()
    metadata.audio_path = audio_file
    metadata.transcript = transcript
    metadata.gender = Gender.FEMALE
    metadata.language_accent = LanguageAccent.EN
    update_transcript(metadata)
buffer.free_storage()