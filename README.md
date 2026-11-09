# ReQuote — AI Procurement Intelligence

ReQuote is a Streamlit MVP for an AI-powered procurement intelligence platform for SMEs.

## What it demonstrates

- Supplier quotation comparison
- Landed-cost calculation
- Supplier scoring
- Price anomaly detection
- Procurement savings analysis
- Basic break-even model
- CSV / Excel quotation upload
- Business dashboard

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, and this `README.md`.
3. Go to Streamlit Community Cloud.
4. Create a new app.
5. Select your repository.
6. Set the main file to `app.py`.
7. Deploy.

No API key is required for this MVP.

## Expected upload format

CSV or Excel with at least:

- Supplier
- Product
- Quantity
- Unit Price

Optional:

- Delivery Fee
- VAT Rate
- Lead Time (days)
- Supplier Reliability

The app also includes a demo dataset so it works immediately after deployment.

## Important academic note

The financial assumptions and demo procurement data are illustrative/synthetic. They should be replaced with survey and/or real-world research data before being presented as evidence of actual market demand.

## Future product roadmap

1. OCR extraction from PDF/image quotations
2. Historical price database
3. ML-based price prediction
4. Supplier reliability learning
5. Automated RFQ creation
6. Purchase-order workflows
7. Supplier marketplace
8. Procurement benchmarking
