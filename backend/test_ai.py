import asyncio
import json
from gemini_service import analyze_product_images

async def main():
    tasks = [{'data': 'https://images.meesho.com/images/products/1038203392/o2fz8_512.jpg', 'is_url': True}]
    res = await analyze_product_images(tasks)
    print("RAW AI OUTPUT:")
    print(json.dumps(res, indent=2))
    
    from rules_engine import validate_and_correct
    validated = validate_and_correct(res[0])
    print("\nVALIDATED OUTPUT:")
    print(json.dumps(validated, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
