"""
Video assessment module — Whisper transcription + communication scoring.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any


async def transcribe_video(file_path: str) -> dict[str, Any]:
    """
    Transcribe a video/audio file using OpenAI Whisper.

    Returns transcribed text and metadata.
    """
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        text: str = result.get("text", "")
        segments = result.get("segments", [])

        return {
            "transcription": text,
            "language": result.get("language", "en"),
            "duration_seconds": segments[-1]["end"] if segments else 0,
            "segment_count": len(segments),
        }
    except Exception as e:
        return {
            "transcription": "",
            "error": str(e),
            "language": "unknown",
            "duration_seconds": 0,
            "segment_count": 0,
        }


def score_communication(transcription: str) -> dict[str, Any]:
    """
    Score communication quality from transcription text.

    Heuristics:
    - Vocabulary richness (unique words / total words)
    - Sentence length diversity
    - Filler word frequency
    - Overall fluency estimate
    """
    if not transcription.strip():
        return {
            "overall_score": 0,
            "vocabulary_richness": 0,
            "filler_ratio": 0,
            "avg_sentence_length": 0,
            "feedback": "No transcription available.",
        }

    words = transcription.lower().split()
    total_words = len(words)
    unique_words = len(set(words))

    filler_words = {"um", "uh", "like", "you know", "basically", "actually", "literally", "so", "well"}
    filler_count = sum(1 for w in words if w in filler_words)

    sentences = [s.strip() for s in transcription.split(".") if s.strip()]
    avg_sentence_length = total_words / max(len(sentences), 1)

    # Scores (0-100)
    vocab_score = min(round(unique_words / max(total_words, 1) * 100, 1), 100)
    filler_ratio = round(filler_count / max(total_words, 1) * 100, 2)
    filler_score = max(100 - filler_ratio * 10, 0)
    length_score = min(100, round(avg_sentence_length * 5, 1))

    overall = round((vocab_score * 0.4 + filler_score * 0.3 + length_score * 0.3), 1)
    overall = min(overall, 100)

    return {
        "overall_score": overall,
        "vocabulary_richness": vocab_score,
        "filler_ratio": filler_ratio,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "total_words": total_words,
        "feedback": _generate_feedback(overall),
    }


def _generate_feedback(score: float) -> str:
    """Generate human-readable feedback based on score."""
    if score >= 80:
        return "Excellent communication skills. Clear, articulate, and well-structured responses."
    elif score >= 60:
        return "Good communication skills. Generally clear with room for minor improvements."
    elif score >= 40:
        return "Average communication skills. Consider reducing filler words and improving vocabulary."
    else:
        return "Communication skills need improvement. Recommend practice with structuring responses."


async def assess_video(file_path: str) -> dict[str, Any]:
    """
    Full video assessment pipeline: transcription → scoring.
    """
    transcription_result = await transcribe_video(file_path)
    text = transcription_result.get("transcription", "")
    communication_scores = score_communication(text)

    return {
        "transcription": transcription_result,
        "communication": communication_scores,
    }
