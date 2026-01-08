# PDF Embedding Setup Instructions

## Overview
The "How It Works" section has been updated to display your full research paper as an embedded PDF document.

## Setup Steps

### 1. Place Your PDF File
Put your 33-page research paper PDF in the `data` folder with the name `research_paper.pdf`:

```
pressure-index/
├── data/
│   ├── duckworth_lewis_table.csv
│   ├── pi-t20.csv
│   └── research_paper.pdf  ← Place your PDF here
```

### 2. File Location
The exact path should be:
```
/Users/rhitankarsmacbook/Downloads/pressure-index/data/research_paper.pdf
```

### 3. What You'll See
Once the PDF is in place, the "How It Works" page will display:
- The introduction text you specified
- The full 33-page PDF embedded directly in the page (1200px height)
- Users can scroll through all pages within the app
- Contact information at the bottom

### 4. If PDF is Not Found
If the PDF file is missing, the app will show:
- An error message indicating the file is not found
- Instructions on where to place the file

## How It Works

The implementation uses:
- **Base64 encoding** to convert the PDF to a data URI
- **HTML iframe** to embed the PDF directly in the Streamlit page
- **Responsive design** with full width and proper height for readability

## PDF Display Features

✅ **Full PDF embedded** - All 33 pages viewable in the app
✅ **Scrollable** - Users can scroll through the entire document
✅ **No external links** - PDF is embedded directly (no external hosting needed)
✅ **Fallback support** - Download link if browser doesn't support PDF viewing
✅ **Clean styling** - Border and rounded corners for professional appearance

## Browser Compatibility

The embedded PDF viewer works in:
- ✅ Chrome/Edge (built-in PDF viewer)
- ✅ Firefox (built-in PDF viewer)
- ✅ Safari (built-in PDF viewer)
- ⚠️ Older browsers may show a download link instead

## Customization Options

If you want to adjust the PDF viewer, you can modify these parameters in `src/pages/how_it_works.py`:

```python
height="1200px"  # Change height (e.g., "1500px" for taller display)
width="100%"     # Keep at 100% for responsive width
```

## Testing

After placing your PDF:
1. Restart the Streamlit app: `streamlit run main.py`
2. Navigate to "How It Works" page
3. You should see the PDF embedded below the introduction text
4. Try scrolling through the pages to ensure it works

## Alternative: Use a Different Filename

If you prefer a different filename, edit line 73 in `src/pages/how_it_works.py`:

```python
pdf_path = os.path.join(base_path, 'data', 'your_custom_name.pdf')
```

## Notes

- The PDF is loaded when the page is accessed, so it may take a moment for large files
- Your 33-page PDF should load fine (typical size ~2-10 MB)
- The base64 encoding increases file size by ~33%, but this is handled automatically
- Users can use browser's print function to print the PDF if needed
