# URL Shortener

## Issues
1) In `main.py` missing all the core endpoints(shorten, redirect and stats)
2) In `models.py` Completely empty, needs data implementation
3) In `utils.py` needs URL validation and short code generation

## Solved Core Features
1) `POST/api/shorten` -URL shortening with validation
2) `GET /<short_code>` -Redirect with click tracking
3) `GET /api/stats/<short_code>` - Analytics endpoint

## Solved Technical problems
4) Thread-safe concurrent request handling
5) character alphanumeric short codes
6) Comprehensive URL validation
7) Proper error handling with meaningful messages and code

## Improved Qualities 
8) Clean separation of concerns
9) Robust input validation
10) Thread safety with locks
11) Edge case handling

### Note:
- Used Clude.ai for error handling and quality features
- Used gemini for clean coding
