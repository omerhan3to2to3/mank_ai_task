# monk_ai_task
A Python script that runs speech to text on WAV file and groups the words into continuous speech segments based on a configurable pause threshold.

Use the command below to run the script.  
You can adjust the `pause_threshold` value (in seconds) to control how sensitive the segment separation should be.
```bash
python process.py --pause_threshold 1.0
