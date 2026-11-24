import io
import uuid

import av
from fastapi import HTTPException
from PIL import Image, ImageOps

from ..models import TicketEvidence, TicketVideoEvidence


MAX_IMAGE_SIZE = 2 * 1024 * 1024
MAX_VIDEO_SIZE = 12 * 1024 * 1024
MAX_VIDEO_SECONDS = 30
MAX_EVIDENCE = 5
VIDEO_CODECS = {"mp4": {"h264", "hevc"}, "webm": {"vp8", "vp9", "av1"}}
AUDIO_CODECS = {"mp4": {"aac", "opus"}, "webm": {"opus", "vorbis"}}
VIDEO_TYPES = {"mp4": "video/mp4", "webm": "video/webm"}
MEDIA_EXTENSIONS = {"image/jpeg": "jpg", "video/mp4": "mp4", "video/webm": "webm"}


def sanitize_image(blob):
    if len(blob) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Evidence images must be at most 2 MB")
    try:
        with Image.open(io.BytesIO(blob), formats=("JPEG", "PNG", "WEBP")) as original:
            if original.width * original.height > 12_000_000 or getattr(original, "n_frames", 1) != 1:
                raise ValueError("Unsupported image")
            original.thumbnail((1600, 1600))
            image = ImageOps.exif_transpose(original).convert("RGB")
            output = io.BytesIO()
            clean = Image.new("RGB", image.size)
            clean.paste(image)
            clean.save(output, format="JPEG", quality=85)
    except (OSError, ValueError, Image.DecompressionBombError) as error:
        raise HTTPException(422, "Upload a valid JPEG, PNG or WebP image under 12 megapixels") from error
    if output.tell() > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Evidence image exceeds the storage limit")
    return output.getvalue()


def video_container(blob):
    if blob[4:8] == b"ftyp":
        return "mp4"
    if blob.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    return None


def open_video(blob, container):
    options = {"protocol_whitelist": "file"}
    if container == "mp4":
        options.update({"enable_drefs": "0", "use_absolute_path": "0"})
    return av.open(io.BytesIO(blob), format="mov" if container == "mp4" else "matroska",
                   options=options)


def sanitize_video(blob, container):
    output = io.BytesIO()
    try:
        with open_video(blob, container) as source:
            if source.duration and source.duration > MAX_VIDEO_SECONDS * av.time_base:
                raise HTTPException(422, "Evidence videos must be at most 30 seconds")
            video = next((stream for stream in source.streams.video
                          if not (stream.disposition & stream.disposition.attached_pic)), None)
            if (video is None or video.codec_context.name not in VIDEO_CODECS[container]
                    or not 0 < video.width * video.height <= 8_300_000):
                raise ValueError("Unsupported video stream")
            audio = next((stream for stream in source.streams.audio
                          if stream.codec_context.name in AUDIO_CODECS[container]), None)
            streams = [video] if audio is None else [video, audio]
            with av.open(output, mode="w", format=container) as target:
                mapped = {}
                for stream in streams:
                    clipped = target.add_stream_from_template(stream)
                    clipped.metadata.clear()
                    mapped[stream.index] = clipped
                video_packets = 0
                for packet in source.demux(*streams):
                    if packet.dts is None or not packet.size:
                        continue
                    if packet.stream.index == video.index:
                        video_packets += 1
                        if video_packets > 4000:
                            raise ValueError("Too many video frames")
                    end = max(packet.dts, packet.pts if packet.pts is not None else packet.dts)
                    if float((end + (packet.duration or 0)) * packet.time_base) > MAX_VIDEO_SECONDS + 0.25:
                        raise HTTPException(422, "Evidence videos must be at most 30 seconds")
                    packet.stream = mapped[packet.stream.index]
                    target.mux(packet)
            if not video_packets:
                raise ValueError("Empty video")
        content = output.getvalue()
        if len(content) > MAX_VIDEO_SIZE:
            raise HTTPException(413, "Evidence videos must be at most 12 MB")
        with open_video(content, container) as check:
            stream = check.streams.video[0]
            stream.codec_context.thread_count = 2
            if next(check.decode(stream), None) is None:
                raise ValueError("Unreadable video")
        return content
    except (av.FFmpegError, ValueError, OverflowError) as error:
        raise HTTPException(422, "Upload a playable MP4, MOV or WebM video") from error


def prepare_evidence(file):
    blob = file.file.read(MAX_VIDEO_SIZE + 1)
    if len(blob) > MAX_VIDEO_SIZE:
        raise HTTPException(413, "Evidence videos must be at most 12 MB")
    container = video_container(blob)
    if container:
        return sanitize_video(blob, container), VIDEO_TYPES[container]
    return sanitize_image(blob), "image/jpeg"


def evidence_record(complaint_id, content, content_type):
    fields = dict(id=str(uuid.uuid4()), complaint_id=complaint_id, size=len(content))
    if content_type == "image/jpeg":
        return TicketEvidence(image=content, **fields)
    return TicketVideoEvidence(data=content, content_type=content_type, **fields)


def evidence_json(record):
    return {"id": record.id, "size": record.size, "created_at": record.created_at,
            "content_type": getattr(record, "content_type", "image/jpeg")}
