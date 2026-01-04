import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.examination_kg_importer import examination_kg_importer

async def main():
    csv_path = "/Users/steve/Desktop/智能体平台/code/MedKG/data/examination_ontology.csv"
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    print(f"Importing from {csv_path}...")
    try:
        stats = await examination_kg_importer.import_from_csv(csv_path, clear_existing=True)
        print("Import Success!")
        print(stats)
    except Exception as e:
        print(f"Import Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
