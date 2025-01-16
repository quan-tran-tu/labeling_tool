# Currently not dealing with async
import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.base import MetadataBuffer, AUDIO_DIR, Metadata

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; replace with specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods; customize as needed
    allow_headers=["*"],  # Allows all headers; customize as needed
)

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
@app.post("/update_transcript/{audio_filename}")
def update_transcript(metadata: Metadata):
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