# Fine Print PDF Scanner

A Streamlit demo that highlights potentially concerning terms in a PDF and gives the analysis a 0–100 concern score. It includes pre-analyzed sample documents that work offline.

## Run locally

```bash
python -m pip install -r requirements.txt
cp .env.example .env  # optional; leave the key blank for sample-only mode
streamlit run main.py
```

Set `OPENAI_API_KEY` in the environment or local `.env` only if you want live scans. Never commit a real key. The app does not persist uploaded documents. If live scans are configured, the app asks for consent and sends extracted PDF text to OpenAI.

## Public demo protections

- Dependency floors require Streamlit 1.54.0 or newer and pypdf 6.19.0 or newer. These versions include upstream fixes for a Windows SSRF issue and recent PDF parser resource-exhaustion issues.
- Streamlit CORS and XSRF protections stay enabled. The Railway demo is embedded from `connors.dev` with an exact origin allowlist and Streamlit's `SameSite=None` XSRF cookie setting; it must be served through HTTPS. Browsers that block third-party cookies can use the full-app link.
- Uploads are limited to 10 MB, 30 pages, and 24,000 extracted text characters. Encrypted PDFs are rejected.
- Live analysis is limited to 3 scans per session and 12 scans per server process per rolling hour. Restarting a process resets the process-wide counter; deploy one app process per instance if relying on this budget.
- Each OpenAI request has a 30-second timeout, no automatic retries, and a 1,000-token response cap. Uploaded document text is treated as untrusted input.
- Without `OPENAI_API_KEY`, uploads are not sent anywhere and only the pre-analyzed samples are available.

The rate limits are an application-level guard, not account authentication or a durable billing quota. Keep the API key out of the public app unless the operator accepts that remaining limitation.

## Deploy on Railway

The `Procfile` binds Streamlit to Railway's `$PORT`, keeps CORS/XSRF enabled, and sets upload/message size limits. Deploy without `OPENAI_API_KEY` for the offline sample demo. Configure the key only through Railway's encrypted service variables if live analysis is intentionally enabled.

## Test

```bash
python -m unittest discover -s tests -v
python -m py_compile main.py scanner.py
```

## Screenshots

![Fine print scanner](https://github.com/user-attachments/assets/e72653aa-d99f-4683-85ea-5068889ca2d5)

![Sample analysis](https://github.com/user-attachments/assets/f6f1a799-3b18-4826-935b-469221c60c41)
