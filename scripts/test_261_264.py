import sys
sys.path.append('src')
try:
    import quadrumvirato_261_264
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
