# PDF → Markdown → Spoken Equations → Audio (Google Colab)

This standalone script is built for **Google Colab free tier** and does:

1. Upload PDF
2. OCR/parse into markdown with equations using `facebook/nougat-base`
3. Find equations and rewrite each into spoken English using `google/flan-t5-base`
4. Generate high-quality speech using `microsoft/speecht5_tts` + HiFiGAN vocoder
5. Save:
   - full document audio (`full_document.wav`)
   - chapter-split audio files (`chapters/*.wav`) based on markdown headings
   - raw markdown + spoken-equation markdown + equation mapping JSON

## Colab usage

Run this in a Colab notebook cell (after cloning this repo into `/content/random-stuff`, or adjust the paths accordingly):

```python
!pip -q install -r /content/random-stuff/pdf_to_audio_colab/requirements.txt
!python /content/random-stuff/pdf_to_audio_colab/colab_pdf_to_audio.py
```

If you skip `--pdf_path`, Colab file upload UI will open.

Optional:

```python
!python /content/random-stuff/pdf_to_audio_colab/colab_pdf_to_audio.py \
  --pdf_path "/content/my_doc.pdf" \
  --output_dir "/content/output_pdf_audio"
```

## Notes

- Best results on Colab with **GPU runtime**.
- `nougat-base` is compute-heavy on long PDFs; free tier can take a while.
- Chapter splitting uses markdown headings (`#`, `##`, etc.) detected in Nougat output.
