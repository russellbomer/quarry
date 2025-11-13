# Quick Test Reference

## 🚀 Run the Wizard

```bash
cd /workspaces/quarry
python -m quarry wizard
```

## 📋 What to Provide

1. **Template**: Choose `custom`
2. **Job name**: Any slug (e.g., `test_site`)
3. **Start URL**: Your target URL
4. **Analyze HTML?**: Say `yes` (y)
5. **Select pattern**: Pick the best match (usually option 1)
6. **Field selectors**: Accept defaults or customize
7. **Allowlist**: Accept default (auto-extracted from URL)
8. **Cursor field**: Usually `url` or `id`
9. **Sink format**: `parquet` (faster) or `csv` (readable)
10. **Output path**: Accept default

## ✅ Success Indicators

**During analysis:**
- ✓ Page title displayed
- ✓ Found 3+ item patterns
- ✓ Field previews show actual data
- ✓ No error messages

**In generated YAML:**
- Specific selectors (classes/IDs, not just `div`)
- Field selectors find the right content
- Item count matches expectation

## ⚠️ Warning Signs

**Error messages:**
- `robots.txt disallows` → Site blocks this URL
- `403 Forbidden` → Bot protection (Cloudflare/Akamai)
- `404 Not Found` → Check URL
- `timeout` → Site slow/unavailable
- `connection` → Network issue

**Detection issues:**
- No patterns found → Try different page
- Only 1-2 items → Not a list page
- Generic selectors (`div`, `span`) → Manual tuning needed
- Preview shows wrong data → Selectors need adjustment

## 🔍 Common Test Scenarios

### News/Forum Sites (EASY)
Examples: Hacker News, Reddit, forums
- Should detect: 20-30 items
- Item selector: `tr.athing`, `div.thing`, `article`
- Fields: title, url, score, date

### Blog Listings (MEDIUM)
Examples: WordPress, Medium, dev blogs
- Should detect: 5-15 items  
- Item selector: `article`, `div.post`
- Fields: title, url, date, author

### E-commerce (HARD)
Examples: Amazon, eBay, product listings
- May struggle with: JS rendering, obfuscated classes
- Bot protection likely (Cloudflare, Akamai)
- Use browser DevTools to inspect first

## 🐛 If Something Breaks

**The wizard should NEVER crash.** If it does:
1. Note the exact error message
2. Note the URL you tried
3. Check if the URL loads in a browser

**Expected failures** (graceful):
- robots.txt blocking → Clear message + continue option
- 403/429 errors → Helpful tips + continue option
- No patterns found → Offers manual selector entry
- Empty/malformed HTML → Safe defaults returned

## 📊 After Wizard: Run the Job

```bash
# Run the generated job
python -m quarry run jobs/YOUR_JOB_NAME.yml

# Check output
ls -lh data/cache/custom/

# View data (Parquet)
python -c "import pandas as pd; df = pd.read_parquet('data/cache/custom/LATEST.parquet'); print(df.head())"
```

## 🎯 What We're Testing

1. **Bot evasion** - Does it get blocked?
2. **Selector detection** - Does it find items?
3. **Field extraction** - Does it get the right data?
4. **Error handling** - Does it fail gracefully?
5. **Edge cases** - Unicode, deep nesting, obfuscated classes?

## 📝 Test Results Template

**URL**: `___________________`

**Site Type**: News / Blog / E-commerce / Other: `_______`

**Bot Evasion**:
- [ ] No 403 errors
- [ ] No 429 errors  
- [ ] robots.txt respected
- [ ] Fetched successfully

**Detection**:
- [ ] Found item patterns (count: `___`)
- [ ] Item selector looks good: `___________________`
- [ ] Fields detected: `___________________`
- [ ] Preview shows correct data

**Issues**:
- Error messages: `___________________`
- Missing fields: `___________________`
- Wrong data extracted: `___________________`

**Overall**: ✅ Success / ⚠️ Needs tuning / ❌ Failed

---

**Good luck testing! 🚀**
