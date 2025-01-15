# Currently not dealing with async
import os
import glob
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; replace with specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods; customize as needed
    allow_headers=["*"],  # Allows all headers; customize as needed
)

AUDIO_DIR = "audio"
METADATA_PATH = "metadata.txt"

# Singleton class to store temporary metadatas
class MetadataBuffer:
    _instance = None
    _max_capacity = 1
    processed_files = set()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MetadataBuffer, cls).__new__(cls)
            cls._instance._init_storage()
        return cls._instance
    
    def _init_storage(self):
        """Initialize storage and capacity"""
        self._load_processed_files()
        self.capacity = 0
        self.storage = []

    def _load_processed_files(self):
        """Load processed files from the metadata file"""
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split('|')
                    if parts:  # Ensure the line is valid
                        self.processed_files.add(parts[0])

    def add_item(self, item: str):
        """
        Add an item to the storage. If capacity exceeds max_capacity, the storage is cleared automatically.
        """ 
        self.storage.append(item)
        self.capacity += 1

        if self.capacity > self._max_capacity:
            self.free_storage()
    def free_storage(self):
        """
        Process the items and clear the storage
        """
        MetadataBuffer.write_metadata(self.storage)
        self.storage = []
        self.capacity = 0
    @classmethod
    def set_max_capacity(cls, max_capacity: int):
        """
        Set the max_capacity of the metadata buffer
        """
        cls._max_capacity = max_capacity
    @staticmethod    
    def write_metadata(storage: list):
        """
        Write the metadatas in the storage to the metadata file once the storage is full
        """
        with open(METADATA_PATH, 'a', encoding='utf-8') as file: 
            for item in storage: 
                file.write(f"{item}\n")

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

class LanguageAccent(Enum):
    VI_C = "vi-c"
    VI_N = "vi-n"
    VI_S = "vi-s"
    EN = "en"

class Metadata(BaseModel):
    gender: Gender
    language_accent: LanguageAccent
    audio_path: str
    transcribe: str

    def get_summary(self) -> str:
        """Return a line to write to metadata file"""
        return '|'.join([self.audio_path, self.gender.value, self.language_accent.value, self.transcribe])

buffer = MetadataBuffer()

# API to get an iterable of audio_filename from audio_dir
@app.get("/get_audio_iterable")
def get_audio_iterable():
    audio_files = []
    try:
        audio_files = glob.glob(f"{AUDIO_DIR}/*.wav")
        audio_filenames = [os.path.basename(file) for file in audio_files]
        unprocessed_files = [file for file in audio_filenames if file not in buffer.processed_files]
        return {"iterable": unprocessed_files}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No files found in {AUDIO_DIR}")

# API to register the transcript labeled for the audio
@app.post("/update_transcribe/{audio_filename}")
def update_transcribe(metadata: Metadata):
    summary = metadata.get_summary()
    buffer.add_item(summary)

# API to write anything left in the buffer storage
@app.post("/release_buffer")
def release_buffer():
    buffer.free_storage()

# API to play the audio file in the frontend
@app.get("/get_audio_file/{filename}")
def get_audio_file(filename: str):
    """
    Serve the requested audio file.
    """
    audio_path = os.path.join(os.getcwd(), "audio", filename)
    if not os.path.isfile(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/wav")