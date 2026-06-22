import argparse
import json
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import fitz
import numpy as np
import soundfile as sf
import torch
from datasets import load_dataset
from PIL import Image
from tqdm.auto import tqdm
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoProcessor,
    NougatProcessor,
    SpeechT5ForTextToSpeech,
    SpeechT5HifiGan,
    SpeechT5Processor,
    VisionEncoderDecoderModel,
)


def log_progress(step: int, total: int, message: str) -> None:
    print(f"[{step}/{total}] {message}", flush=True)


def get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def try_colab_upload() -> str:
    try:
        from google.colab import files  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "--pdf_path not provided and this is not running in Google Colab."
        ) from exc
    uploaded = files.upload()
    if not uploaded:
        raise RuntimeError("No file uploaded.")
    filename = next(iter(uploaded.keys()))
    return filename


def pdf_to_images(pdf_path: str, dpi: int = 180) -> List[Image.Image]:
    doc = fitz.open(pdf_path)
    images: List[Image.Image] = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        mode = "RGB"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()
    return images


def extract_markdown_with_nougat(
    images: List[Image.Image], device: torch.device
) -> str:
    processor = NougatProcessor.from_pretrained("facebook/nougat-base")
    model = VisionEncoderDecoderModel.from_pretrained("facebook/nougat-base").to(device)
    model.eval()

    pages_md: List[str] = []
    for image in tqdm(images, desc="Nougat OCR", unit="page"):
        pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
        with torch.no_grad():
            outputs = model.generate(
                pixel_values,
                min_length=1,
                max_new_tokens=2048,
                bad_words_ids=[[processor.tokenizer.unk_token_id]],
            )
        page_text = processor.batch_decode(outputs, skip_special_tokens=True)[0]
        pages_md.append(page_text.strip())
    return "\n\n".join(pages_md).strip()


EQ_PATTERNS = [
    re.compile(r"\$\$(.+?)\$\$", flags=re.DOTALL),
    re.compile(r"\\\[(.+?)\\\]", flags=re.DOTALL),
    re.compile(r"\\\((.+?)\\\)", flags=re.DOTALL),
    re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", flags=re.DOTALL),
]


@dataclass
class EquationMatch:
    raw: str
    inner: str
    start: int
    end: int


def collect_equations(markdown_text: str) -> List[EquationMatch]:
    matches: List[EquationMatch] = []
    occupied: List[Tuple[int, int]] = []

    def overlaps(s: int, e: int) -> bool:
        return any(not (e <= os_ or s >= oe) for os_, oe in occupied)

    for pattern in EQ_PATTERNS:
        for m in pattern.finditer(markdown_text):
            s, e = m.span()
            if overlaps(s, e):
                continue
            occupied.append((s, e))
            matches.append(
                EquationMatch(raw=m.group(0), inner=m.group(1).strip(), start=s, end=e)
            )
    matches.sort(key=lambda x: x.start)
    return matches


def verbalize_equations(
    equations: List[EquationMatch], device: torch.device
) -> List[str]:
    processor = AutoProcessor.from_pretrained("google/flan-t5-base")
    model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base").to(device)
    model.eval()

    spoken: List[str] = []
    for eq in tqdm(equations, desc="Equation verbalization", unit="eq"):
        prompt = textwrap.dedent(
            f"""
            Convert this LaTeX equation into natural spoken English for text-to-speech.
            Keep it concise and readable.
            Equation: {eq.inner}
            Spoken:
            """
        ).strip()
        inputs = processor(prompt, return_tensors="pt", truncation=True, max_length=512).to(
            device
        )
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=96,
                do_sample=False,
                num_beams=4,
                early_stopping=True,
            )
        verbal = processor.batch_decode(out, skip_special_tokens=True)[0].strip()
        spoken.append(verbal if verbal else eq.inner)
    return spoken


def replace_equations_with_spoken(
    markdown_text: str, equations: List[EquationMatch], spoken_texts: List[str]
) -> str:
    if not equations:
        return markdown_text
    chunks: List[str] = []
    cursor = 0
    for eq, spoken in zip(equations, spoken_texts):
        chunks.append(markdown_text[cursor : eq.start])
        chunks.append(f"[Equation spoken form: {spoken}]")
        cursor = eq.end
    chunks.append(markdown_text[cursor:])
    return "".join(chunks)


def split_by_headings(markdown_text: str) -> List[Tuple[str, str]]:
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$", flags=re.MULTILINE)
    matches = list(heading_re.finditer(markdown_text))
    if not matches:
        return [("chapter_01_full_document", markdown_text.strip())]

    chapters: List[Tuple[str, str]] = []
    if matches[0].start() > 0:
        pre = markdown_text[: matches[0].start()].strip()
        if pre:
            chapters.append(("chapter_00_preface", pre))

    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
        content = markdown_text[start:end].strip()
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower() or f"chapter_{i+1:02d}"
        chapters.append((f"chapter_{i+1:02d}_{slug}", content))
    return chapters


def text_chunks(text: str, max_chars: int = 350) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    pieces = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current = ""
    for piece in pieces:
        if len(current) + len(piece) + 1 <= max_chars:
            current = f"{current} {piece}".strip()
        else:
            if current:
                chunks.append(current)
            if len(piece) <= max_chars:
                current = piece
            else:
                forced = textwrap.wrap(piece, width=max_chars, break_long_words=False)
                chunks.extend(forced[:-1])
                current = forced[-1] if forced else ""
    if current:
        chunks.append(current)
    return chunks


def build_tts(device: torch.device):
    processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
    model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(device)
    vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(device)
    model.eval()
    vocoder.eval()
    embeddings_ds = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
    speaker_embedding = torch.tensor(embeddings_ds[7306]["xvector"]).unsqueeze(0).to(device)
    return processor, model, vocoder, speaker_embedding


def synthesize_text(
    text: str, tts_processor, tts_model, vocoder, speaker_embedding, device: torch.device
) -> np.ndarray:
    chunks = text_chunks(text)
    if not chunks:
        return np.zeros((1,), dtype=np.float32)

    audio_parts: List[np.ndarray] = []
    pause = np.zeros((3200,), dtype=np.float32)  # 0.2s at 16kHz

    for chunk in tqdm(chunks, desc="TTS chunks", unit="chunk", leave=False):
        inputs = tts_processor(text=chunk, return_tensors="pt").to(device)
        with torch.no_grad():
            speech = tts_model.generate_speech(
                inputs["input_ids"], speaker_embedding, vocoder=vocoder
            )
        audio_parts.append(speech.cpu().numpy().astype(np.float32))
        audio_parts.append(pause)
    return np.concatenate(audio_parts, axis=0)


def save_audio(path: Path, audio: np.ndarray, sample_rate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, samplerate=sample_rate, subtype="PCM_24")


def run(pdf_path: str, output_dir: str) -> None:
    total_steps = 7
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = get_device()

    log_progress(1, total_steps, f"Using device: {device}")
    images = pdf_to_images(pdf_path)
    if not images:
        raise RuntimeError("No pages found in PDF.")

    log_progress(2, total_steps, f"Extracting markdown from {len(images)} pages with Nougat...")
    raw_markdown = extract_markdown_with_nougat(images, device)
    (out_dir / "markdown_raw.md").write_text(raw_markdown, encoding="utf-8")

    log_progress(3, total_steps, "Finding equations in markdown...")
    equations = collect_equations(raw_markdown)
    print(f"Found {len(equations)} equations.", flush=True)

    log_progress(4, total_steps, "Converting equations into spoken form...")
    spoken_equations = verbalize_equations(equations, device) if equations else []
    spoken_markdown = replace_equations_with_spoken(raw_markdown, equations, spoken_equations)
    (out_dir / "markdown_spoken_equations.md").write_text(spoken_markdown, encoding="utf-8")

    eq_export = [
        {"index": i + 1, "latex": eq.inner, "spoken": spoken_equations[i]}
        for i, eq in enumerate(equations)
    ]
    (out_dir / "equations_spoken.json").write_text(
        json.dumps(eq_export, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    log_progress(5, total_steps, "Splitting markdown into chapter sections...")
    chapters = split_by_headings(spoken_markdown)
    print(f"Generated {len(chapters)} chapter section(s).", flush=True)

    log_progress(6, total_steps, "Loading TTS model and generating chapter audio...")
    tts_processor, tts_model, vocoder, speaker_embedding = build_tts(device)

    chapter_audio_dir = out_dir / "chapters"
    full_audio_parts: List[np.ndarray] = []
    chapter_break = np.zeros((16000,), dtype=np.float32)  # 1 second

    for chapter_name, chapter_text in tqdm(chapters, desc="Chapters", unit="chapter"):
        audio = synthesize_text(
            chapter_text, tts_processor, tts_model, vocoder, speaker_embedding, device
        )
        chapter_path = chapter_audio_dir / f"{chapter_name}.wav"
        save_audio(chapter_path, audio)
        full_audio_parts.append(audio)
        full_audio_parts.append(chapter_break)

    all_audio = np.concatenate(full_audio_parts, axis=0) if full_audio_parts else np.zeros((1,))

    log_progress(7, total_steps, "Saving full-document audio...")
    save_audio(out_dir / "full_document.wav", all_audio.astype(np.float32))

    print("\nDone.", flush=True)
    print(f"Output directory: {out_dir.resolve()}", flush=True)
    print(f"- Raw markdown: {out_dir / 'markdown_raw.md'}", flush=True)
    print(f"- Spoken markdown: {out_dir / 'markdown_spoken_equations.md'}", flush=True)
    print(f"- Equation map: {out_dir / 'equations_spoken.json'}", flush=True)
    print(f"- Chapters audio dir: {chapter_audio_dir}", flush=True)
    print(f"- Full audio: {out_dir / 'full_document.wav'}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Google Colab pipeline: PDF -> Nougat markdown -> spoken equations -> TTS audio."
    )
    parser.add_argument(
        "--pdf_path",
        type=str,
        default=None,
        help="Path to PDF. If omitted in Colab, a file upload dialog is shown.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output_pdf_audio",
        help="Directory to save markdown and audio outputs.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    pdf_path = args.pdf_path or try_colab_upload()
    run(pdf_path=pdf_path, output_dir=args.output_dir)
