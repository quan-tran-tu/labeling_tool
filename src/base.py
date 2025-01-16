import os
from enum import Enum

AUDIO_DIR = "audio"
METADATA_PATH = "metadata.txt"

# Singleton class to store temporary metadatas
class MetadataBuffer:
    _instance = None
    _max_capacity = 100
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

try:
    from pydantic import BaseModel
except ImportError:
    # Define a dummy base class if pydantic is not available
    class BaseModel:
        pass

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
    transcript: str

    def get_summary(self) -> str:
        """Return a line to write to metadata file"""
        return '|'.join([self.audio_path, self.gender.value, self.language_accent.value, self.transcript])
