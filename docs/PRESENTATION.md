# Final Presentation — Japan Car Import Advisory Platform

## Slide 1: Title
**Japan Car Import Advisory Platform**
Helping Kenyan buyers decide: Import from Japan or buy locally?

---

## Slide 2: Problem Statement
- Used cars in Kenya are often expensive due to local dealer markups
- Importing from Japan can save 20–40%, but total cost is hard to estimate
- Buyers need: purchase price + shipping + KRA taxes + port/clearing/registration fees

---

## Slide 3: Solution Overview
End-to-end platform with:
1. Data extraction from 5 Japanese car platforms
2. Database storage & ETL cleaning
3. Import cost calculator (Kenya-specific)
4. ML price prediction model
5. Interactive web dashboard (HTML/CSS/JS + FastAPI)

---

## Slide 4: Data Sources
| Platform | URL |
|----------|-----|
| SBT Japan | sbtjapan.com |
| Car From Japan | carfromjapan.com |
| AAAJapan | aaajapan.com |
| JapaneseCarTrade | japanesecartrade.com |
| BE FORWARD | beforward.jp |

Filter: vehicles manufactured **2018 onwards**

---

## Slide 5: Data Pipeline
```
Scrapers → Raw CSV → ETL Cleaner → SQLite DB → ML Training → Web App
```

Key ETL steps:
- Filter year ≥ 2018
- Remove invalid/missing prices
- Normalize fuel, transmission, body type
- Deduplicate listings
- Convert JPY → USD

---

## Slide 6: Database Schema
Three main tables:
- **car_listings** — scraped vehicle data
- **local_market_prices** — Kenyan market estimates
- **import_cost_estimates** — calculated import breakdowns

---

## Slide 7: Import Cost Calculator
**CIF = FOB + Shipping + Insurance**

Kenya taxes applied on CIF:
- Import Duty: 25%
- Excise: 10–35% (engine size dependent)
- VAT: 16%
- RDL: 2%
- IDF: 2.25%

Plus: port charges, clearing fees, NTSA registration

---

## Slide 8: Example Calculation
**Toyota Harrier 2020 — USD 8,000**

| Item | Amount |
|------|--------|
| Purchase | $8,000 |
| Shipping + Insurance | ~$1,070 |
| KRA Taxes | ~KES 650,000 |
| Port + Clearing + Reg | ~KES 120,000 |
| **Total Landed** | **~KES 1.9M** |
| Local Market | ~KES 2.4M |
| **Savings** | **~KES 500,000** |

---

## Slide 9: Machine Learning Model
- **Algorithm:** XGBoost Regressor
- **Target:** Price in JPY
- **Features:** make, model, year, mileage, engine_cc, fuel, transmission, body, platform
- **Encoding:** One-hot for categoricals
- **Metrics:** R², RMSE, MAE

---

## Slide 10: Dashboard Demo
Live demo of web app (http://localhost:8000):
1. Compare Cars — select vehicle, see import vs local price
2. ML Price Predictor
3. Market Data explorer
4. Savings Analysis charts

---

## Slide 11: Tech Stack
- **Language:** Python 3.11
- **Package manager:** uv
- **Database:** SQLite (PostgreSQL-ready)
- **ML:** XGBoost, scikit-learn
- **Web:** FastAPI, HTML, CSS, JavaScript, Chart.js
- **Scraping:** Requests, BeautifulSoup, Playwright

---

## Slide 12: Challenges & Mitigations
| Challenge | Mitigation |
|-----------|------------|
| Sites block scrapers | Sample data generator + fallback |
| Exchange rate volatility | Configurable via .env |
| Tax rate changes | Modular KRA calculator |
| Sparse local market data | Estimated prices from import cost |

---

## Slide 13: Future Improvements
- Real-time exchange rate API
- Scrape Kenyan platforms (Cheki, Jiji) for local prices
- Playwright-based JS rendering for dynamic sites
- User accounts and saved comparisons
- Mobile app

---

## Slide 14: Conclusion
Built a complete data engineering + ML platform that:
- Extracts and cleans car listing data
- Calculates full Kenya import costs
- Predicts Japan car prices
- Shows import vs local savings visually

**Run:** `uv run python main.py all`
