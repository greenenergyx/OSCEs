# OSCEs

This repository contains a Streamlit application to generate interactive radiology OSCE cases.

## Files

- `streamlit_app.py`: Streamlit app for generating OSCE-style radiology cases.
- `requirements.txt`: Python dependencies required to run the app.

## Usage

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:

```bash
streamlit run streamlit_app.py
```

3. In the app sidebar, upload or provide paths to:
   - `Radiopaedia_Library.xlsx`
   - `sample_radiopedia_articles.csv`

4. Configure generation settings and click `Generate OSCE cases`.

## Notes

- The default data folder is set to `/content/drive/MyDrive/Gem` for compatibility with Google Drive-mounted Colab environments.
- The app can generate cases from the loaded dataset, including hidden answers and an optional marking grid.
