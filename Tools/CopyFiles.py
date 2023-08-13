import os, sys
import subprocess

def main():
    path = "/scratch/hlim1/Pin/DiWi/benchmark/llvmbugs"
    dirs = os.listdir(path)

    for d in dirs:
        d_path = f"{path}/{d}"
        if os.path.isdir(d_path):
            bug_id = d.split('g')[-1]
            files = os.listdir(d_path)
            for f in files:
                f_path = f"{d_path}/{f}"
                if f.endswith('.c'):
                    subprocess.run(['cp', f_path, f"./llvm_bug{bug_id}.c"])

if __name__ == "__main__":
    main()
