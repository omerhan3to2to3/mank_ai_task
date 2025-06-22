import argparse
from faster_whisper import WhisperModel
from datetime import timedelta
import pandas as pd
import os

def format_time(seconds):
    return str(timedelta(seconds=seconds))[:-3]

def match_speaker(text, df):
    for _, row in df.iterrows():
        if pd.isna(row['Turkish']):
            continue
        if row['Turkish'] in text:
            return row.get('character', 'Unknown')
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

    # Her durumda dosyayı sıfırdan oluştur (varsa üzerine yazar)
    output_rows = []
    for seg in speech_segments:
        start = format_time(seg[0].start)
        text = ' '.join([w.word for w in seg])
        output_rows.append({'timing': start, 'Turkish': text})

    df_new = pd.DataFrame(output_rows)
    df_new.to_excel("text1_log.xlsx", index=False)
    print("✅ 'text1_log.xlsx' dosyası sıfırdan oluşturuldu ve yazıldı.")

    # Eşleştirme ve terminal çıktısı
    df = pd.read_excel("text1_log.xlsx")
    for idx, seg in enumerate(speech_segments, 1):
        start = seg[0].start
        end = seg[-1].end
        text = ' '.join([w.word for w in seg])
        speaker = match_speaker(text, df)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pause_threshold', type=float, required=True, help="Pause threshold in seconds")
    args = parser.parse_args()
    main(args.pause_threshold)
