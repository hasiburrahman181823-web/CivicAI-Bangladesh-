"""
CivicAI Bangladesh - Automated Setup & Seeding Script
Executes full initialization pipeline:
1. Curated Multilingual Dataset Compilation (BanglaPSG Aligned)
2. Model Training & Evaluation (Category, Severity, Multilingual F1)
3. Database Migration & Realistic Bangladesh Data Seeding
"""

import os
import sys
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

def run_step(title, command):
    print(f"\n=======================================================")
    print(f">> [STEP] {title}")
    print(f"=======================================================")
    res = subprocess.run(command, cwd=base_dir, shell=True)
    if res.returncode != 0:
        print(f"[ERROR] Step failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[SUCCESS] {title} completed successfully.")

def main():
    print("Initiating CivicAI Bangladesh Platform Initialization...")
    run_step("Compiling Curated Multilingual Dataset", "python datasets/generate_curated_dataset.py")
    run_step("Training & Evaluating AI Models (Bangla, English, Banglish)", "python training/train_models.py")
    run_step("Seeding Database with Realistic Administrative Records", "python database/seed_data.py")
    run_step("Running Automated QA & API Test Suite", "python -m unittest tests/test_api_and_ai.py")
    print("\n🎉 CivicAI Bangladesh Platform is fully set up, trained, seeded, and tested!")

if __name__ == "__main__":
    main()
