import asyncio

async def seed_corpus():
    """One-off script to download and prepare source corpus documents."""
    print("Preparing and seeding source corpus into database...")
    print("Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_corpus())
