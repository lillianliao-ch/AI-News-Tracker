import os
import glob

directory = "/Users/lillianliao/notion_rag/skill_research/multimodal_jds/"
files = glob.glob(os.path.join(directory, "JD_*.txt"))

chunk_size = 15
for i in range(0, len(files), chunk_size):
    chunk_files = files[i:i + chunk_size]
    chunk_num = i // chunk_size + 1
    with open(os.path.join(directory, f"MEGA_CHUNK_{chunk_num}.txt"), "w", encoding="utf-8") as outfile:
        outfile.write(f"# JD BATCH {chunk_num}\n\n")
        for f in chunk_files:
            # We want to clearly demarcate the individual JDs within the mega chunk
            outfile.write("========================================\n")
            outfile.write(f"Source file: {os.path.basename(f)}\n")
            with open(f, "r", encoding="utf-8") as infile:
                outfile.write(infile.read())
            outfile.write("\n========================================\n\n")

print(f"Aggregated {len(files)} files into {len(files)//chunk_size + 1} MEGA CHUNK files.")
