"""Tests for services/elevenlabs_tts.py — TTS and timestamp logic."""

import pytest
from unittest.mock import patch, MagicMock

from services.elevenlabs_tts import (
    _split_sentences,
    _build_sentence_timestamps,
    _get_client,
    generate_podcast_audio,
    VOICE_ID,
    MODEL_ID,
    OUTPUT_FORMAT,
)


# ── _split_sentences ─────────────────────────────────────────────────────────

class TestSplitSentences:
    def test_single_sentence(self):
        result = _split_sentences("Hello world.")
        assert result == ["Hello world."]

    def test_multiple_sentences(self):
        result = _split_sentences("Hello. How are you? I am fine!")
        assert result == ["Hello.", "How are you?", "I am fine!"]

    def test_empty_string(self):
        result = _split_sentences("")
        assert result == []

    def test_whitespace_only(self):
        result = _split_sentences("   ")
        assert result == []

    def test_no_punctuation(self):
        result = _split_sentences("Hello world")
        assert result == ["Hello world"]

    def test_trailing_whitespace_stripped(self):
        result = _split_sentences("  Hello world.  ")
        assert result == ["Hello world."]

    def test_multiple_spaces_between_sentences(self):
        result = _split_sentences("First.    Second.    Third.")
        assert result == ["First.", "Second.", "Third."]

    def test_exclamation_and_question(self):
        result = _split_sentences("Wow! Really? Yes.")
        assert result == ["Wow!", "Really?", "Yes."]

    def test_abbreviations_may_split(self):
        # The regex splits on sentence-ending punctuation followed by whitespace
        # This is expected behavior — abbreviations may cause splits
        result = _split_sentences("Dr. Smith went home.")
        # "Dr." followed by space triggers a split
        assert len(result) >= 1

    def test_newlines_in_text(self):
        result = _split_sentences("Hello.\nWorld.")
        # \n is whitespace, so it acts as separator
        assert "Hello." in result
        assert "World." in result

    def test_long_text(self):
        text = ". ".join([f"Sentence {i}" for i in range(100)]) + "."
        result = _split_sentences(text)
        assert len(result) == 100

    def test_single_character_sentences(self):
        result = _split_sentences("A. B. C.")
        assert len(result) == 3


# ── _build_sentence_timestamps ───────────────────────────────────────────────

class TestBuildSentenceTimestamps:
    def test_basic(self):
        text = "Hello. World."
        sentences = ["Hello.", "World."]
        starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
        ends = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]

        result = _build_sentence_timestamps(text, sentences, starts, ends)
        assert len(result) == 2
        assert result[0]["text"] == "Hello."
        assert result[1]["text"] == "World."

    def test_timestamps_correct_start_end(self):
        text = "Hi. Bye."
        sentences = ["Hi.", "Bye."]
        # text:   H  i  .     B  y  e  .
        # index:  0  1  2  3  4  5  6  7
        starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        ends = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75]

        result = _build_sentence_timestamps(text, sentences, starts, ends)
        assert result[0]["start"] == 0.0   # 'H' starts at 0
        assert result[0]["end"] == 0.25    # '.' ends at index 2
        assert result[1]["start"] == 0.4   # 'B' starts at index 4
        assert result[1]["end"] == 0.75    # '.' ends at index 7

    def test_empty_sentences(self):
        result = _build_sentence_timestamps("Hello.", [], [0.0], [0.1])
        assert result == []

    def test_sentence_not_found(self):
        text = "Hello."
        sentences = ["Missing sentence."]
        starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
        ends = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

        result = _build_sentence_timestamps(text, sentences, starts, ends)
        assert result == []

    def test_clamp_to_array_bounds(self):
        text = "Hello world!"
        sentences = ["Hello world!"]
        # Very short arrays — should clamp indices
        starts = [0.0, 0.5]
        ends = [0.5, 1.0]

        result = _build_sentence_timestamps(text, sentences, starts, ends)
        assert len(result) == 1
        # start_i = min(0, 1) = 0 -> 0.0
        # end_i = min(11, 1) = 1 -> 1.0
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 1.0

    def test_single_sentence(self):
        text = "One."
        sentences = ["One."]
        starts = [0.0, 0.1, 0.2, 0.3]
        ends = [0.1, 0.2, 0.3, 0.4]

        result = _build_sentence_timestamps(text, sentences, starts, ends)
        assert len(result) == 1
        assert result[0]["text"] == "One."
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 0.4  # end of '.'

    def test_preserves_order(self):
        text = "A. B. C."
        sentences = ["A.", "B.", "C."]
        starts = [float(i) for i in range(len(text))]
        ends = [float(i + 1) for i in range(len(text))]

        result = _build_sentence_timestamps(text, sentences, starts, ends)
        assert len(result) == 3
        assert result[0]["start"] < result[1]["start"] < result[2]["start"]


# ── _get_client ──────────────────────────────────────────────────────────────

class TestGetClient:
    def test_raises_without_api_key(self):
        with patch("services.elevenlabs_tts.ELEVENLABS_API_KEY", None):
            with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY not set"):
                _get_client()

    def test_creates_client_with_key(self):
        with patch("services.elevenlabs_tts.ELEVENLABS_API_KEY", "test-key"):
            with patch("services.elevenlabs_tts.ElevenLabs") as mock_cls:
                client = _get_client()
                mock_cls.assert_called_once_with(api_key="test-key")


# ── generate_podcast_audio ───────────────────────────────────────────────────

class TestGeneratePodcastAudio:
    @pytest.mark.asyncio
    async def test_returns_audio_with_timestamps(self):
        mock_alignment = MagicMock()
        mock_alignment.character_start_times_seconds = [float(i) * 0.1 for i in range(20)]
        mock_alignment.character_end_times_seconds = [float(i) * 0.1 + 0.05 for i in range(20)]

        mock_response = MagicMock()
        mock_response.audio_base_64 = "base64audiodata=="
        mock_response.alignment = mock_alignment

        with patch("services.elevenlabs_tts._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.text_to_speech.convert_with_timestamps.return_value = mock_response
            mock_get_client.return_value = mock_client

            with patch("services.elevenlabs_tts.asyncio.to_thread", side_effect=lambda fn, **kw: fn(**kw)):
                result = await generate_podcast_audio("Hello. World.")

        assert result["audio_base64"] == "base64audiodata=="
        assert len(result["sentences"]) > 0

    @pytest.mark.asyncio
    async def test_fallback_without_alignment(self):
        mock_response = MagicMock()
        mock_response.audio_base_64 = "base64data=="
        mock_response.alignment = None

        with patch("services.elevenlabs_tts._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.text_to_speech.convert_with_timestamps.return_value = mock_response
            mock_get_client.return_value = mock_client

            with patch("services.elevenlabs_tts.asyncio.to_thread", side_effect=lambda fn, **kw: fn(**kw)):
                result = await generate_podcast_audio("Hello. World.")

        assert result["audio_base64"] == "base64data=="
        # Fallback timestamps should all be 0
        for s in result["sentences"]:
            assert s["start"] == 0
            assert s["end"] == 0

    @pytest.mark.asyncio
    async def test_language_code_passed_for_non_english(self):
        mock_response = MagicMock()
        mock_response.audio_base_64 = "data"
        mock_response.alignment = None

        with patch("services.elevenlabs_tts._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.text_to_speech.convert_with_timestamps.return_value = mock_response
            mock_get_client.return_value = mock_client

            with patch("services.elevenlabs_tts.asyncio.to_thread", side_effect=lambda fn, **kw: fn(**kw)):
                await generate_podcast_audio("Hola.", language="es")

            # convert_with_timestamps is called directly by the lambda unwrapping to_thread
            call_kwargs = mock_client.text_to_speech.convert_with_timestamps.call_args
            assert call_kwargs[1]["language_code"] == "es"

    @pytest.mark.asyncio
    async def test_english_no_language_code(self):
        mock_response = MagicMock()
        mock_response.audio_base_64 = "data"
        mock_response.alignment = None

        with patch("services.elevenlabs_tts._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.text_to_speech.convert_with_timestamps.return_value = mock_response
            mock_get_client.return_value = mock_client

            with patch("services.elevenlabs_tts.asyncio.to_thread", side_effect=lambda fn, **kw: fn(**kw)):
                await generate_podcast_audio("Hello.", language="en")

            call_kwargs = mock_client.text_to_speech.convert_with_timestamps.call_args
            assert "language_code" not in call_kwargs[1]


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_voice_id_is_string(self):
        assert isinstance(VOICE_ID, str)
        assert len(VOICE_ID) > 0

    def test_model_id_is_string(self):
        assert isinstance(MODEL_ID, str)

    def test_output_format_is_mp3(self):
        assert "mp3" in OUTPUT_FORMAT
