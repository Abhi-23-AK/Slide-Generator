import requests
import json

url = "http://127.0.0.1:8000/generate-json"
data = {
    "topic": "Cloud Microservices",
    "slide_count": 5,
    "tone": "Technical"
}

response = requests.post(url, data=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 200:
    result = response.json()
    print(f"\nSession ID: {result.get('session_id')}")
    print(f"Number of slides: {len(result.get('slides', []))}")
    
    # Find architecture slide
    for i, slide in enumerate(result.get('slides', [])):
        if 'architecture' in slide.get('slide_type', '').lower() or 'drawio_xml' in slide:
            print(f"\nArchitecture slide found at index {i}")
            print(f"Slide type: {slide.get('slide_type')}")
            print(f"Title: {slide.get('title')}")
            if 'drawio_xml' in slide:
                xml = slide['drawio_xml']
                print(f"XML length: {len(xml)}")
                print(f"XML preview: {xml[:200]}")
                # Save XML for testing
                with open('e:/Slide_Generator/arch_slide.xml', 'w', encoding='utf-8') as f:
                    f.write(xml)
                print("Saved to arch_slide.xml")
else:
    print("Failed to generate deck")
