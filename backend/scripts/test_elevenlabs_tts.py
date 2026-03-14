"""
ElevenLabs TTS Test Script
--------------------------
Standalone script to explore the ElevenLabs text-to-speech API.
Converts a podcast script (text file or built-in sample) to an MP3 audio file.

Usage:
    python backend/scripts/test_elevenlabs_tts.py                           # sample text
    python backend/scripts/test_elevenlabs_tts.py --list-voices             # see available voices
    python backend/scripts/test_elevenlabs_tts.py -i script.txt -o out.mp3  # from file
    python backend/scripts/test_elevenlabs_tts.py --streaming               # streaming mode
"""

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_TEXT = """\
Hey there, welcome back to StatementPod, your personal financial breakdown! \
I'm your host, and today we're diving deep into your latest bank statement data. \
Grab a coffee, get comfortable, because we've got a lot to unpack.

Let's start with the big picture. This month, your total income came in at \
fifty-two hundred dollars. Not bad at all. Now, your total expenses landed at \
around thirty-eight hundred, which means you've got a net savings of fourteen \
hundred dollars. That's a savings rate of about twenty-seven percent, which is \
genuinely impressive. Most financial advisors recommend saving at least twenty \
percent, so you're actually beating that benchmark. Give yourself a pat on the back.

Now let's break down where your money actually went, because that's where things \
get interesting. Your biggest spending category, and this won't surprise most \
people, was Food and Dining. You spent about nine hundred and twenty dollars \
there. That includes groceries, restaurants, coffee shops, all of it. Now, \
nine hundred might sound like a lot, but when you break it down, that's about \
thirty dollars a day. If you're feeding a family, that's actually pretty \
reasonable. If it's just you, there might be some room to trim. One tip I always \
share: try meal prepping on Sundays. Even just preparing lunches for the work \
week can save you a hundred to a hundred fifty dollars a month easily.

Coming in second was Housing and Utilities at eight hundred and fifty dollars. \
That covers your rent or mortgage contribution, electricity, water, internet, \
the essentials. This is pretty stable month to month, which is good. Not much \
you can do to optimize here unless you're up for renegotiating your internet \
plan or switching energy providers, which honestly, a lot of people don't \
realize you can do.

Third on the list is Transportation at four hundred and ten dollars. That \
includes gas, parking, maybe a car payment or transit pass. If you're driving, \
gas prices have been a bit wild lately, so this number might fluctuate. If \
you have the option to work from home even one or two days a week, that could \
chip away at this category pretty meaningfully.

Now here's something I want to flag. Your Subscriptions and Memberships category \
came in at a hundred and forty-five dollars. That might not sound like much, \
but let's annualize it. That's over seventeen hundred dollars a year on \
subscriptions. I'd encourage you to do a quick audit. Do you actually use all \
of those services? A lot of us sign up for free trials and forget to cancel. \
Even cutting two or three unused subscriptions could save you thirty to fifty \
bucks a month.

On the positive side, your Entertainment spending was only about sixty-five \
dollars. That tells me you're being pretty mindful about discretionary spending, \
which is great. And your Healthcare costs were minimal this month at forty \
dollars, which is always nice to see.

Let's talk about your top merchants for a second. Your biggest single merchant \
was a grocery store where you spent three hundred and twenty dollars across \
eight visits. Then there's a gas station at a hundred and ninety over six fill-ups. \
And third was an online retailer at a hundred and fifty across three orders. \
Nothing alarming there, but it's always useful to see exactly where the money \
flows.

Looking at the month-over-month trend, your expenses have actually decreased by \
about five percent compared to last month. Your income stayed flat, which means \
your savings rate improved. That's the kind of trend you want to see. Small, \
consistent improvements add up to big results over time.

So here are my three actionable tips for next month. Number one: tackle that \
subscription audit I mentioned. Pull up your bank statement, highlight every \
recurring charge, and ask yourself if you truly use it. Number two: try the \
meal prep approach. Even starting small, like prepping just lunches, can make a \
difference. And number three: consider setting up an automatic transfer to a \
savings account right when your paycheck hits. Even if it's just fifty or a \
hundred dollars, automating your savings means you won't even miss it.

Overall, you're in a really solid position. Twenty-seven percent savings rate, \
spending that's trending downward, and no major red flags in your transaction \
history. Keep this momentum going, stay intentional with your spending, and \
you'll be in even better shape next month.

That's all for this episode of StatementPod. Thanks for tuning in, and we'll \
catch you next time with your updated financial snapshot. Until then, keep \
making smart money moves!
"""

# Minimal sample for testing when credits are low
SHORT_SAMPLE_TEXT = "Welcome to StatementPod! Your finances are looking great this month."

# Popular voice IDs — run --list-voices to see all available voices
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George
DEFAULT_MODEL = "eleven_multilingual_v2"     # up to 10,000 chars, good quality
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_api_key() -> str:
    """Load ELEVENLABS_API_KEY from backend/.env, exit with message if missing."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"[env] Loaded from {env_path}")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print(
            "\nError: ELEVENLABS_API_KEY not found in environment.\n"
            f"Add it to {env_path}\n"
            "  ELEVENLABS_API_KEY=your-key-here"
        )
        sys.exit(1)
    return api_key


def list_voices(client: ElevenLabs) -> None:
    """Print a table of available voices."""
    print("\nFetching available voices...\n")
    response = client.voices.get_all()

    print(f"{'Name':<25} {'Voice ID':<30} {'Category':<15}")
    print("-" * 70)
    for voice in response.voices:
        category = getattr(voice, "category", "n/a") or "n/a"
        print(f"{voice.name:<25} {voice.voice_id:<30} {category:<15}")
    print(f"\nTotal: {len(response.voices)} voices")


def load_text(input_path: str | None, short: bool = False) -> str:
    """Load text from a file or fall back to SAMPLE_TEXT."""
    if input_path:
        path = Path(input_path)
        if not path.exists():
            print(f"\nError: Input file not found: {path}")
            sys.exit(1)
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            print(f"\nError: Input file is empty: {path}")
            sys.exit(1)
        print(f"[input] Read {len(text)} chars from {path}")
        return text

    if short:
        print("[input] Using SHORT built-in sample (saves credits)")
        return SHORT_SAMPLE_TEXT

    print("[input] Using built-in sample text")
    return SAMPLE_TEXT


def print_summary(text: str, args: argparse.Namespace) -> None:
    """Print a summary of what we're about to do."""
    est_words = len(text.split())
    est_minutes = est_words / 150  # ~150 wpm for narration
    print(f"\n{'='*50}")
    print(f"  Characters : {len(text):,}")
    print(f"  Words      : {est_words:,}")
    print(f"  Est. audio : {est_minutes:.1f} min")
    print(f"  Voice ID   : {args.voice}")
    print(f"  Model      : {args.model}")
    print(f"  Stability  : {args.stability}")
    print(f"  Similarity : {args.similarity}")
    print(f"  Speed      : {args.speed}")
    print(f"  Mode       : {'streaming' if args.streaming else 'non-streaming'}")
    print(f"  Output     : {args.output}")
    print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# TTS functions
# ---------------------------------------------------------------------------

def convert_non_streaming(client: ElevenLabs, text: str, args: argparse.Namespace) -> None:
    """Generate audio using the non-streaming convert endpoint."""
    print("[tts] Calling ElevenLabs convert (non-streaming)...")
    start = time.time()

    audio = client.text_to_speech.convert(
        text=text,
        voice_id=args.voice,
        model_id=args.model,
        output_format=DEFAULT_OUTPUT_FORMAT,
        voice_settings={
            "stability": args.stability,
            "similarity_boost": args.similarity,
            "speed": args.speed,
        },
    )

    # audio is a generator of bytes chunks — collect and write
    output_path = Path(args.output)
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    elapsed = time.time() - start
    size_kb = output_path.stat().st_size / 1024
    print(f"[tts] Done in {elapsed:.1f}s")
    print(f"[tts] Saved to {output_path} ({size_kb:.1f} KB)")


def convert_streaming(client: ElevenLabs, text: str, args: argparse.Namespace) -> None:
    """Generate audio using the streaming endpoint."""
    print("[tts] Calling ElevenLabs stream (streaming)...")
    start = time.time()

    audio_stream = client.text_to_speech.stream(
        text=text,
        voice_id=args.voice,
        model_id=args.model,
        output_format=DEFAULT_OUTPUT_FORMAT,
        voice_settings={
            "stability": args.stability,
            "similarity_boost": args.similarity,
            "speed": args.speed,
        },
    )

    output_path = Path(args.output)
    total_bytes = 0
    chunk_count = 0

    with open(output_path, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)
            total_bytes += len(chunk)
            chunk_count += 1
            if chunk_count % 10 == 0:
                print(f"  ... received {chunk_count} chunks ({total_bytes / 1024:.1f} KB)")

    elapsed = time.time() - start
    print(f"[tts] Done in {elapsed:.1f}s — {chunk_count} chunks, {total_bytes / 1024:.1f} KB")
    print(f"[tts] Saved to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ElevenLabs TTS test script for StatementPod",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--input", help="Path to a text file with the podcast script")
    parser.add_argument("-o", "--output", default="output.mp3", help="Output MP3 path (default: output.mp3)")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE_ID, help=f"Voice ID (default: {DEFAULT_VOICE_ID})")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--list-voices", action="store_true", help="List available voices and exit")
    parser.add_argument("--stability", type=float, default=0.5, help="Voice stability 0-1 (default: 0.5)")
    parser.add_argument("--similarity", type=float, default=0.75, help="Similarity boost 0-1 (default: 0.75)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed 0.5-2.0 (default: 1.0)")
    parser.add_argument("--streaming", action="store_true", help="Use streaming API instead of convert")
    parser.add_argument("--short", action="store_true", help="Use a minimal sample text (saves credits)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = load_api_key()
    client = ElevenLabs(api_key=api_key)

    if args.list_voices:
        list_voices(client)
        return

    text = load_text(args.input, args.short)
    print_summary(text, args)

    try:
        if args.streaming:
            convert_streaming(client, text, args)
        else:
            convert_non_streaming(client, text, args)
    except Exception as e:
        error_msg = str(e)
        if "quota_exceeded" in error_msg:
            print(
                f"\nError: Quota exceeded. Your text needs more credits than you have remaining."
                f"\n  Text length: {len(text)} chars"
                f"\n  Try: --short flag to use a minimal sample, or upgrade your ElevenLabs plan."
            )
        elif "401" in error_msg or "Unauthorized" in error_msg:
            print("\nError: Invalid API key. Check ELEVENLABS_API_KEY in backend/.env")
        elif "404" in error_msg or "not found" in error_msg.lower():
            print(f"\nError: Voice ID '{args.voice}' not found. Run with --list-voices to see available voices")
        elif "429" in error_msg or "rate" in error_msg.lower():
            print("\nError: Rate limited by ElevenLabs. Wait a moment and try again")
        else:
            print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
