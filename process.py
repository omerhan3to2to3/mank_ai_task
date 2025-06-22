import argparse
from faster_whisper import WhisperModel
from datetime import timedelta, datetime
import pandas as pd
import os
from difflib import SequenceMatcher

# 🕒 Formatlama yardımcıları
def format_time(seconds):
    """Float saniyeyi HH:MM:SS.ms formatına çevirir."""
    return str(timedelta(seconds=seconds))[:-3]

def parse_time(s):
    """Zaman stringini datetime nesnesine çevirir."""
    try:
        return datetime.strptime(s, "%H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(s, "%H:%M:%S")

# 🧠 Karakter eşleştirme mantığı
def best_match(text_row, ref_df, offset, window=3, threshold=0.7):
    """
    - `offset`: text2_log ile reference_log arasındaki zaman farkı
    - `window`: +/- saniye toleransı
    - `threshold`: metin benzerliği oranı
    """
    start = parse_time(text_row["start_time"]) + offset
    best_score = 0
    best_char = "Unknown"

    for _, row in ref_df.iterrows():
        try:
            ref_time = parse_time(str(row["TIMING"]))
            if abs((ref_time - start).total_seconds()) <= window:
                score = SequenceMatcher(None, text_row["Turkish"].lower(), str(row["TURKISH"]).lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_char = row["CHARACTER"]
        except:
            continue

    return best_char if best_score >= threshold else "Unknown"

# 🧩 Ana işlem
def main(pause_threshold):
    model = WhisperModel("guillaumekln/faster-whisper-base", compute_type="int8", device="cuda")
    print("🔁 Transkripsiyon başlatılıyor...")
    segments, _ = model.transcribe("Sakirpasa.wav", word_timestamps=True)

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

    # 📄 Referans dosyasını yükle
    ref_df = pd.read_excel("reference_log.xlsx")

    # 🕐 text2_log ile reference_log arasında zaman farkı (örnek olarak: +1 saat 11 dakika 38 saniye)
    offset = timedelta(hours=1, minutes=11, seconds=38)

    # 📊 Yeni dosyayı oluştur
    output_rows = []
    for seg in speech_segments:
        start_sec = seg[0].start
        end_sec = seg[-1].end
        start = format_time(start_sec)
        end = format_time(end_sec)
        text = ' '.join([w.word for w in seg])
        print(seg)
        row = {'start_time': start, 'end_time': end, 'Turkish': text}
        row['character'] = best_match(row, ref_df, offset)
        output_rows.append(row)

    df_new = pd.DataFrame(output_rows)
    df_new.to_excel("text2_log.xlsx", index=False)
    print("✅ 'text2_log.xlsx' dosyası güncellendi.")

# 🚀 Komut satırı argümanları
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pause_threshold', type=float, required=True, help="Pause threshold in seconds")
    args = parser.parse_args()
    main(args.pause_threshold)
