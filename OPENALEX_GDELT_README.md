# OpenAlex GDELT Data Extraction Protocol

This document outlines the procedure for extracting a complete bibliometric dataset from OpenAlex for all research related to GDELT.

## 1. Search Strategy
- **Endpoint:** `https://api.openalex.org/works`
- **Filter:** `fulltext.search:GDELT`
- **Logic:** This searches the full text of over 60 million works (PDFs and n-grams) for the term "GDELT".

## 2. Technical Implementation Details

### Deep Paging (Cursor-based)
To handle more than 10,000 records (though this set is ~685), we use **cursor-based pagination**.
- Initial request: `cursor=*`
- Subsequent requests: Use the `next_cursor` value returned in the previous response's metadata.
- `per_page` is set to `200` to minimize API calls.

### Entity Enrichment ("All Tables")
The "Works" record contains basic info, but for "Full Metadata," we perform secondary fetches for every unique entity mentioned.
1. **Extraction:** Parse every work to collect unique IDs for:
   - **Authors** (`A...`)
   - **Institutions** (`I...`)
   - **Sources/Journals** (`S...`)
   - **Topics** (`T...`)
   - **Publishers** (`P...`)
   - **Funders** (`F...`)
2. **Batch Fetching:** Use the `filter=openalex:ID1|ID2|...` syntax to fetch records in batches of 50. This is significantly faster than individual requests.

### Robustness Measures
- **Polite Pool:** Includes a `mailto` parameter in all headers to ensure priority queueing.
- **None-Check Logic:** Explicitly handles cases where `primary_location` or `source` fields are `null` to prevent script crashes.
- **Rate Limiting:** `time.sleep(0.1)` between calls to respect OpenAlex's standard limit (100ms per request).

## 3. Data Structure
The dataset is saved in `openalex_gdelt_full_dataset/`:
- `gdelt_works.json`: Consolidated file containing all ~685 work records (Cossack format).
- `authors/`: Individual JSONs for every unique author profile.
- `institutions/`: Individual JSONs for every unique university/research center.
- `sources/`: Individual JSONs for journals and conferences.
- `topics/`: Full topic metadata.
- `funders/`: Grant-providing organization metadata.

## 4. How to Reproduce
Run the provided `reproduce_openalex_gdelt.py` script. It is self-contained and requires only the `requests` library.
