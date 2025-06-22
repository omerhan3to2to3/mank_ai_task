import argparse
from faster_whisper import WhisperModel
from datetime import timedelta
import pandas as pd
import os
from difflib import SequenceMatcher

def format_time(seconds):
    return str(timedelta(seconds=seconds))[:-3]

def parse_time_str(time_str):
    """HH:MM:SS.ms → saniye (float)"""
    t = time_str.split(":")
    seconds = float(t[-1])
    minutes = int(t[-2])
    hours = int(t[-3]) if len(t) == 3 else 0
    return hours * 3600 + minutes * 60 + seconds

def match_speaker_hybrid(start, end, text, df, similarity_threshold=0.8):
    # 1. Zaman aralığına göre eşleşme
    if "start_time" in df.columns and "end_time" in df.columns:
        for _, row in df.iterrows():
            try:
                t_start = parse_time_str(str(row["start_time"]))
                t_end = parse_time_str(str(row["end_time"]))
                if t_start <= start <= t_end or t_start <= end <= t_end:
                    return row.get("character", "Unknown")
            except:
                continue

    # 2. Metin benzerliği ile eşleşme (fuzzy matching)
    best_match = None
    best_score = 0
    for _, row in df.iterrows():
        ref = str(row.get("Turkish", "")).lower()
        score = SequenceMatcher(None, text.lower(), ref).ratio()
        if score > best_score:
            best_score = score
            best_match = row

    if best_score >= similarity_threshold:
        return best_match.get("character", "Unknown")

    return "Unknown"

def main(pause_threshold):
    model = WhisperModel("guillaumekln/faster-whisper-base", compute_type="int8")
    print("🔁 Transkripsiyon başlatılıyor...")
    segments, _ = model.transcribe("Sakirpasa.wav", word_timestamps=True)

    # Segmentlere ayır
    speech_segments = []
    current = []
    last_end = 0.0

    for seg in segments:
        for word in seg.words:
            if current and (word.start - last_end > pause_threshold):
                speech_segments.append(current)
                current = []
            current.append(word)
            last_end = word.end
    if current:
        speech_segments.append(current)

# Her zaman text_log.xlsx dosyasını sıfırdan oluştur
    output_rows = []
    for seg in speech_segments:
        start_sec = seg[0].start
        end_sec = seg[-1].end
        start = format_time(start_sec)
        end = format_time(end_sec)
        text = ' '.join([w.word for w in seg])

        output_rows.append({
            'start_time': start,
            'end_time': end,
            'Turkish': text
        })

    df_new = pd.DataFrame(output_rows)
    df_new.to_excel("text2_log.xlsx", index=False)
    print("✅ 'text_log.xlsx' dosyası sıfırdan oluşturuldu ve güncellendi.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pause_threshold', type=float, required=True, help="Pause threshold in seconds")
    args = parser.parse_args()
    main(args.pause_threshold)
