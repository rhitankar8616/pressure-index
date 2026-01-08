# SSL Certificate Fix - macOS

## Problem
When trying to load the CSV from Dropbox, you may encounter an SSL certificate error:
```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

## Solution Applied

### 1. Fixed SSL Certificates ✅
Ran the Python certificate installer:
```bash
bash "/Applications/Python 3.12/Install Certificates.command"
```

This updates the certifi package and creates the proper SSL certificate symlinks.

### 2. Updated CSV Loader
Modified `src/utils/csv_loader.py` to:
- Use `requests` library instead of pandas' URLopen (better SSL handling)
- Add fallback to local `data/pi-t20.csv` for development
- Provide helpful error messages with fix instructions
- Cache downloaded files locally

### 3. Loading Priority
The CSV loader now tries in this order:
1. **Cache** (`~/.cache/pressure_index/pi-t20.csv`) - Fastest
2. **Local file** (`data/pi-t20.csv`) - For development
3. **Dropbox** (URL) - For deployment

## For Local Development

### Option A: Use Local CSV (Recommended for Testing)
1. Download the CSV from Dropbox manually
2. Place it in `data/pi-t20.csv`
3. App will load it instantly

### Option B: Fix SSL and Use Dropbox
Already done! Certificates are now updated.

## For Deployment (Streamlit Cloud)

**No changes needed!** Streamlit Cloud has proper SSL certificates, so Dropbox loading will work automatically.

## Testing

Try running the app now:
```bash
streamlit run main.py
```

The app should now:
- Load from Dropbox successfully (SSL fixed)
- Or load from local `data/pi-t20.csv` if present
- Cache the data for future runs

## If Still Having Issues

### Quick Test
```python
import requests
url = "https://www.dropbox.com/scl/fi/ngtum2qeh8q727dlwfpxj/pi-t20.csv?rlkey=vjt63fwe4jzb6ewvilorl0252&st=12ydinys&dl=1"
response = requests.get(url, timeout=10)
print(f"Status: {response.status_code}")
print(f"Size: {len(response.content)} bytes")
```

If this works, the app will work.

### Alternative: Use Local File
For local testing, you can simply:
1. Keep `pi-t20.csv` in the `data/` folder
2. Add it to `.gitignore` (already done)
3. App will use it automatically
4. When deployed to Streamlit Cloud, it will use Dropbox

## Environment Notes

- **Python Version**: 3.12
- **SSL Certificates**: Updated to certifi 2026.1.4
- **Requests Library**: Already in requirements.txt
- **Cache Location**: `~/.cache/pressure_index/`

## Next Steps

1. ✅ SSL certificates fixed
2. ✅ CSV loader updated with fallbacks
3. ✅ Ready to test locally
4. ✅ Ready to deploy to Streamlit Cloud

The app is now configured to work both locally and on Streamlit Cloud!
