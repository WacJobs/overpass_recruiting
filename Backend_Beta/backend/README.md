# Overpass Recruiting Backend (TF-IDF + Industry Labeling)

This version adds an admin-only industry-labeling pipeline:

- Bootstrap official 2022 NAICS 2-digit sectors
- Use GPT to weak-label company website text into NAICS sectors
- Review or auto-approve labels
- Fit a TF-IDF + Multinomial Naive Bayes industry classifier
- Predict industries for companies in bulk
- Use industry alignment as an extra feature in match scoring

## New admin flow

1. `POST /api/admin/industry/bootstrap-naics`
2. `POST /api/admin/industry/labels/generate`
3. optionally `POST /api/admin/industry/labels/review`
4. `POST /api/admin/industry/model/fit`
5. `POST /api/admin/industry/model/predict-companies`
6. `POST /api/matches/score-text`

## Admin auth

If you set `ADMIN_API_KEY`, send it as:

`X-Admin-Key: your-key-here`

If left blank in local development, the admin industry routes remain open.

## Notes

The GPT labeler currently uses the OpenAI Responses API and asks the model to return strict JSON. If you want stricter schema enforcement or cheaper large-scale labeling, this is the right place to swap in structured outputs and/or Batch later.
