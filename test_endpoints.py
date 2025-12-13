import requests

endpoints = [
    # Admin Pages
    'http://localhost:7878/admin/',
    'http://localhost:7878/admin/products',
    'http://localhost:7878/admin/reservations',
    'http://localhost:7878/admin/quotations',
    
    # Customer Pages
    'http://localhost:7878/customer/',
    'http://localhost:7878/customer/products/1',
]

print(f"🔍 Testing {len(endpoints)} endpoints")
failures = []

for url in endpoints:
    try:
        response = requests.get(url, timeout=5)
        status = response.status_code
        if status == 200:
            print(f"[✅] {url.replace('http://localhost:7878', '')}: 200")
        else:
            print(f"[❌] {url.replace('http://localhost:7878', '')}: {status}")
            failures.append(f"{url.replace('http://localhost:7878', '')}: HTTP {status}")
            
    except Exception as e:
        print(f"[❌] {url}: {e}")
        failures.append(f"{url}: {e}")

print("\n=== SUMMARY ===")
if failures:
    print(f"⚠️  {len(failures)} FAILURES:")
    for f in failures:
        print(f"  - {f}")
    exit(1)
else:
    print("✅ ALL TESTS PASSED")
    exit(0)
