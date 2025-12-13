import subprocess
import time
import requests
import sys
import os
import signal

# Configuration
BASE_URL = "http://localhost:7878"
ENDPOINTS = [
    '/admin/',
    '/admin/products',
    '/admin/products/new',
    '/admin/products/1', # Mock ID
    '/admin/reservations',
    '/admin/reservations/RES-2025-001', # Mock ID
    '/admin/quotations',
    '/admin/quotations/new',
    '/admin/quotations/Q-2025-001', # Mock ID
    '/admin/payments',
    '/admin/finance',
    '/admin/flights',
    '/admin/hotels',
    '/admin/attractions',
    '/admin/partners',
    '/admin/partners/new',
    '/admin/customers',
    '/admin/settings',
    '/customer/',
    '/customer/products/1', # Mock ID (assuming DB has data or handles 404 gracefully)
]

def start_server():
    print("🚀 Starting Flask Server...")
    # Use Popen to start in background
    # Ensure usage of the correct python environment if possible, but 'python' should work as alias
    process = subprocess.Popen([sys.executable, 'app.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process

def wait_for_server():
    print("⏳ Waiting for server to be ready...")
    retries = 30
    for _ in range(retries):
        try:
            requests.get(BASE_URL)
            print("✅ Server is UP!")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    print("❌ Server failed to start.")
    return False

def check_encoding(text):
    # Common mojibake markers
    bad_markers = ['Ã©', 'Ã¼', '???', 'ï¿½', 'ì•ˆë…•'] 
    # Note: '???' is tricky because it might be valid text, but in this context (Korean webapp) 
    # a sequence of literal question marks often indicates encoding loss if it replaces Hangul.
    # However, user mentioned "????" specifically.
    
    # Also check for unrendered jinja
    if '{{' in text and '}}' in text:
        # Check if it's inside code block? unlikely in rendered HTML unless it's a tutorial
        return "Jinja2 Template Error (Unrendered Tags)"

    for marker in bad_markers:
        if marker in text:
            return f"Encoding Error (Found '{marker}')"
    
    # Check for correct korean charset meta if korean char exists?
    # Actually just check basic moji logic
    return None

def run_tests():
    results = []
    print(f"🔍 Testing {len(ENDPOINTS)} endpoints...")
    
    for endpoint in ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        status = "UNKNOWN"
        error = None
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            
            if status == 200:
                enc_error = check_encoding(response.text)
                if enc_error:
                    error = enc_error
                    status = f"200 ({enc_error})"
            elif status == 404:
                error = "Not Found"
            elif status == 500:
                error = "Internal Server Error"
            else:
                error = f"Status {status}"
                
        except Exception as e:
            status = "ERROR"
            error = str(e)
            
        print(f"[{'✅' if status == 200 else '❌'}] {endpoint}: {status}")
        results.append({
            'endpoint': endpoint,
            'status': status,
            'error': error
        })
        
    return results

def main():
    server_process = start_server()
    
    try:
        if wait_for_server():
            results = run_tests()
            
            # Print Report
            print("\n" + "="*30)
            print("       QA Report       ")
            print("="*30)
            failed_count = 0
            for r in results:
                if r['error']:
                    print(f"❌ {r['endpoint']}: {r['status']} - {r['error']}")
                    failed_count += 1
            
            if failed_count == 0:
                print("🎉 All checks passed!")
            else:
                print(f"⚠️  {failed_count} issues found.")
                
            # Keep server running for a bit if we want to confirm log output? 
            # No, kill it.
        else:
            # Print stderr to see why it failed
            stdout, stderr = server_process.communicate(timeout=5)
            print("STDOUT:", stdout)
            print("STDERR:", stderr)

    finally:
        print("🛑 Stopping Server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()

if __name__ == "__main__":
    main()
