import os
import subprocess

# Input and Output folder paths
input_folder = "Capstone"
output_folder = "CapstoneC"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".mov"):
        input_file = os.path.join(input_folder, filename)
        output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.mp4")

        command = [
            "ffmpeg", "-i", input_file, "-c:v", "libx264", "-preset", "slow",
            "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", output_file
        ]

        print(f"Converting: {filename} -> {output_file}")
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("✅ Batch conversion complete!")