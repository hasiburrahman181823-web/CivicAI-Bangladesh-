"""Create a reproducible derived English view using a local Marian CT2 model."""
import argparse
import csv
from pathlib import Path

import ctranslate2
from transformers import MarianTokenizer

from backend.ml_training.scripts.train_text import read_data

def translate(args):
    tokenizer = MarianTokenizer.from_pretrained(args.model, local_files_only=True)
    model = ctranslate2.Translator(str(args.model), device="cpu", compute_type="int8", intra_threads=4)
    rows = read_data(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if args.output.exists():
        with args.output.open(encoding="utf-8") as previous:
            completed = {int(row["row_id"]) for row in csv.DictReader(previous) if row["english"].strip()}
    rows = [row for row in rows if row[0] not in completed]
    with args.output.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not f.tell():
            writer.writerow(["row_id","english","source_type"])
        for start in range(0,len(rows),32):
            batch = rows[start:start+32]
            ids = tokenizer([x[1] for x in batch], truncation=True, max_length=180)["input_ids"]
            tokens = [tokenizer.convert_ids_to_tokens(row) for row in ids]
            translations = model.translate_batch(tokens, beam_size=1, max_decoding_length=180)
            for (index, *_), result in zip(batch, translations, strict=True):
                ids = tokenizer.convert_tokens_to_ids(result.hypotheses[0])
                writer.writerow([index,tokenizer.decode(ids,skip_special_tokens=True),"derived"])
            f.flush()
            if start % 320 == 0:
                print(f"Translated {min(start+32,len(rows))}/{len(rows)} remaining rows",flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--workbook",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    translate(parser.parse_args())
