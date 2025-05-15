"""
Script to load memories for all characters
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.memory.characters.iron_man.wiki_loader import main as load_iron_man
from app.memory.characters.thor.wiki_loader import main as load_thor

async def main():
    """Load memories for all characters"""
    print("=== Loading memories for Iron Man ===")
    await load_iron_man()
    
    print("\n=== Loading memories for Thor ===")
    await load_thor()
    
    print("\n=== All memories loaded successfully ===")

if __name__ == "__main__":
    asyncio.run(main()) 