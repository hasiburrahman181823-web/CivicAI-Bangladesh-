"""End-to-end smoke test with actual trained and pretrained model assets."""
import argparse
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

def verify(image, audio):
    with tempfile.TemporaryDirectory() as scratch:
        os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(scratch)/"qa.db")
        from fastapi.testclient import TestClient
        from backend.app.main import app
        with TestClient(app) as api:
            health=api.get("/api/health").json()
            assert health["classification"] == "trained" and health["embeddings"]
            assert health["voice"] and health["image"]
            payload={"title":"ময়লার সমস্যা", "text":"এলাকার রাস্তায় ময়লা ফেলা হচ্ছে। বর্জ্য সরানোর ব্যবস্থা করুন।",
                     "area":"Dhaka", "language":"Bangla",
                     "occurred_at":(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()}
            analysis=api.post("/api/analyze",json=payload)
            assert analysis.status_code==200, analysis.text
            summary=analysis.json()
            assert summary["models"]["severity"]["label"] in {"Low","Medium","High"}
            assert 0<summary["confidence"]<=1 and summary["requires_review"]
            assert "duplicates" not in summary
            complaint=api.post("/api/complaints",json=payload).json()
            assert complaint["analysis"]["models"] == summary["models"]
            retrieval=api.post(f'/api/track/{complaint["id"]}',json={"tracking_key":complaint["tracking_key"]})
            assert retrieval.status_code==200
            image_result=api.post("/api/media/road-image",files={"file":("road.jpg",image.read_bytes(),"image/jpeg")})
            assert image_result.status_code==200 and "detections" in image_result.json(), image_result.text
            audio_result=api.post("/api/media/transcribe?language=en",files={"file":(audio.name,audio.read_bytes(),"audio/wav")})
            assert audio_result.status_code==200 and audio_result.json()["text"], audio_result.text
            forecast=api.get("/api/research/closure-benchmark",params={"category":"Road","occurred_at":payload["occurred_at"]})
            assert forecast.status_code==200 and forecast.json()["source"]=="NYC 311 historical benchmark"
            print("Real model endpoints passed: classification, calibrated output, submission, tracking, vision, voice, forecast.")
            print("Image detections:", len(image_result.json()["detections"]))
            print("Voice transcript characters:",len(audio_result.json()["text"]))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image",type=Path,required=True)
    parser.add_argument("--audio",type=Path,required=True)
    args=parser.parse_args()
    verify(args.image,args.audio)
