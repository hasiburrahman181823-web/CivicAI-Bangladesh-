import io
from functools import lru_cache
from threading import BoundedSemaphore

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from starlette.datastructures import UploadFile
from starlette.concurrency import run_in_threadpool

from ..ml.predict import ARTIFACTS

router = APIRouter(prefix="/api/media", tags=["media"])
inference_slot = BoundedSemaphore(1)

@lru_cache(maxsize=1)
def speech_model():
    from faster_whisper import WhisperModel
    return WhisperModel(str(ARTIFACTS/"whisper"),device="cpu",compute_type="int8",cpu_threads=2,local_files_only=True)

def transcribe(raw, language=None):
    import av
    frames = []
    total = 0
    audio_format = identify_audio(raw)
    if audio_format is None:
        raise ValueError("Unsupported audio format")
    with av.open(io.BytesIO(raw), format=audio_format, options={"protocol_whitelist":"file,pipe"}) as media:
        if not media.streams.audio or len(media.streams)>2:
            raise ValueError("No audio stream")
        if media.duration is not None and media.duration / av.time_base > 61:
            raise ValueError("Audio must be at most 60 seconds")
        resampler = av.AudioResampler(format="s16", layout="mono",rate=16000)
        for chunk in media.decode(audio=0):
            for frame in resampler.resample(chunk):
                data = frame.to_ndarray().reshape(-1)
                total += len(data)
                if total > 60*16000:
                    raise ValueError("Audio must be at most 60 seconds")
                frames.append(data)
        for frame in resampler.resample(None):
            data = frame.to_ndarray().reshape(-1)
            total += len(data)
            if total > 60*16000:
                raise ValueError("Audio must be at most 60 seconds")
            frames.append(data)
    if not frames:
        raise ValueError("File contains no audio")
    audio = np.concatenate(frames).astype(np.float32)/32768
    segments, info = speech_model().transcribe(audio, language=language, beam_size=3, vad_filter=True,
                                              condition_on_previous_text=False)
    return {"text":" ".join(segment.text.strip() for segment in segments).strip(),
            "language":info.language,"model":"Whisper tiny multilingual","review_required":True}

def identify_audio(raw):
    if raw.startswith(b"RIFF") and raw[8:12] == b"WAVE":
        return "wav"
    if raw.startswith(b"fLaC"):
        return "flac"
    if raw.startswith(b"OggS"):
        return "ogg"
    if raw.startswith(b"ID3") or (len(raw)>2 and raw[0]==0xff and raw[1]&0xe0==0xe0):
        return "mp3"
    if raw[4:8] == b"ftyp":
        return "mov"
    if raw.startswith(b"\x1a\x45\xdf\xa3"):
        return "matroska"
    return None

async def read_upload(request, limit):
    if not request.headers.get("content-type","").lower().startswith("multipart/form-data;"):
        raise HTTPException(415,"Select a supported media file")
    async with request.form(max_files=1,max_fields=0,max_part_size=1024) as form:
        file=form.get("file")
        if not isinstance(file,UploadFile):
            raise HTTPException(422,"Exactly one file is required")
        raw=await file.read(limit+1)
        if len(raw)>limit:
            raise HTTPException(413,"File exceeds the allowed size")
        return raw

@router.post("/transcribe")
async def voice(request: Request, language: str | None=None):
    if not (ARTIFACTS/"whisper/model.bin").is_file():
        raise HTTPException(503,"Voice weights are not installed")
    if language not in {None,"bn","en"}:
        raise HTTPException(422,"Select Bangla, English or automatic detection")
    if not inference_slot.acquire(blocking=False):
        raise HTTPException(429,"Media analysis is busy. Please retry shortly.")
    try:
        raw=await read_upload(request,8*1024*1024)
        import av
        try:
            return await run_in_threadpool(transcribe, raw, language)
        except (ValueError,av.error.FFmpegError):
            raise HTTPException(422,"Use a supported, readable audio file of at most 60 seconds")
    finally:
        inference_slot.release()

def infer_image(raw):
    from PIL import Image, UnidentifiedImageError
    from ..ml.road import detect_road_damage
    try:
        with Image.open(io.BytesIO(raw), formats=["JPEG","PNG","WEBP"]) as source:
            if source.width * source.height > 12_000_000 or getattr(source,"n_frames",1)!=1:
                raise ValueError("Unsupported image")
            return detect_road_damage(source)
    except (UnidentifiedImageError, Image.DecompressionBombError, ValueError, OSError):
        raise HTTPException(422,"Use a readable, single-frame JPEG, PNG or WebP of up to 12 megapixels")

@router.post("/road-image")
async def road(request: Request):
    if not (ARTIFACTS/"road/road.onnx").is_file():
        raise HTTPException(503,"Road damage detector weights are not installed")
    if not inference_slot.acquire(blocking=False):
        raise HTTPException(429,"Media analysis is busy. Please retry shortly.")
    try:
        raw=await read_upload(request,6*1024*1024)
        return await run_in_threadpool(infer_image,raw)
    finally:
        inference_slot.release()
