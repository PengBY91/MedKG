#!/usr/bin/env python3
"""
Examination Ontology Import Script
导入检查项目本体数据到Neo4j知识图谱
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.examination_kg_importer import examination_kg_importer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main import function."""
    
    # Default CSV file path
    default_csv = Path(__file__).parent.parent.parent / "data" / "examination_ontology.csv"
    
    # Get CSV file path from command line or use default
    if len(sys.argv) > 1:
        csv_file = Path(sys.argv[1])
    else:
        csv_file = default_csv
    
    # Check if file exists
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        logger.info(f"Usage: python {sys.argv[0]} <path_to_csv>")
        sys.exit(1)
    
    logger.info(f"Starting import from: {csv_file}")
    
    # Determine if we should clear existing data
    clear_existing = "--clear" in sys.argv or "-c" in sys.argv
    
    if clear_existing:
        logger.warning("Will clear existing data before import!")
        # confirm = input("Are you sure? (yes/no): ")
        # if confirm.lower() != "yes":
        #    logger.info("Import cancelled")
        #    sys.exit(0)
    
    try:
        # Import data
        stats = await examination_kg_importer.import_from_csv(
            str(csv_file),
            clear_existing=clear_existing
        )
        
        # Display results
        logger.info("=" * 60)
        logger.info("Import completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Level 1 body parts created: {stats['level1_nodes']}")
        logger.info(f"Level 2 body parts created: {stats['level2_nodes']}")
        logger.info(f"Examination methods created: {stats['method_nodes']}")
        logger.info(f"Modalities created: {stats['modality_nodes']}")
        logger.info("-" * 60)
        logger.info(f"HAS_SUBPART relationships: {stats['has_subpart_rels']}")
        logger.info(f"SUPPORTS_METHOD relationships: {stats['supports_method_rels']}")
        logger.info(f"USES_MODALITY relationships: {stats['uses_modality_rels']}")
        logger.info("=" * 60)
        
        # Verification queries
        logger.info("\nVerification queries:")
        logger.info("1. View all nodes:")
        logger.info("   MATCH (n) RETURN labels(n), count(*)")
        logger.info("\n2. View sample paths:")
        logger.info("   MATCH path = (l1:BodyPartLevel1)-[:HAS_SUBPART]->")
        logger.info("                (l2:BodyPartLevel2)-[:SUPPORTS_METHOD]->")
        logger.info("                (m:ExaminationMethod)")
        logger.info("   RETURN l1.name, l2.name, m.name LIMIT 10")
        
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Display usage
    print("=" * 60)
    print("Examination Ontology Import Script")
    print("=" * 60)
    print(f"Usage: python {sys.argv[0]} [csv_file] [--clear]")
    print()
    print("Options:")
    print("  csv_file    Path to CSV file (default: ../examination_ontology.csv)")
    print("  --clear     Clear existing data before import")
    print("=" * 60)
    print()
    
    # Run import
    asyncio.run(main())
