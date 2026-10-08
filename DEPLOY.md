# 🚀 Vercel Deployment Guide

Quick guide to deploy all three projects to Vercel.

## Prerequisites

- [Vercel account](https://vercel.com/signup) (free tier sufficient)
- Repository connected to Vercel

## 📋 Exact Vercel Settings

Each project deploys as a **separate Vercel project** with Root Directory set to its subfolder.

### 1. Excel Automation

```
Project Name: excel-automation-demo (or your choice)
Framework Preset: Other
Root Directory: excel-automation [IMPORTANT: Click Edit → Select folder]
Build Command: [leave empty]
Install Command: pip install -r requirements.txt
Environment Variables: None required
```

**Function Settings** (auto-configured via vercel.json):
- Max Duration: 30s
- Memory: 1024MB

**Post-Deploy Test**:
```bash
curl https://your-deployment.vercel.app/health
# Expected: {"status":"healthy","service":"excel-automation"}

curl https://your-deployment.vercel.app/sample
# Should return JSON with processed Excel data
```

---

### 2. PDF Document AI

```
Project Name: pdf-document-ai-demo (or your choice)
Framework Preset: Other
Root Directory: pdf-document-ai [IMPORTANT: Click Edit → Select folder]
Build Command: [leave empty]
Install Command: pip install -r requirements.txt
Environment Variables: 
  - OPENAI_API_KEY (optional - works without it in heuristic mode)
  - OPENAI_MODEL (optional - defaults to gpt-4o-mini)
```

**Function Settings** (auto-configured via vercel.json):
- Max Duration: 30s
- Memory: 1024MB

**Post-Deploy Test**:
```bash
curl https://your-deployment.vercel.app/health
# Expected: {"status":"healthy","service":"pdf-document-ai","ai_mode":"heuristic"}

curl https://your-deployment.vercel.app/sample
# Should return JSON with extracted contract data
```

---

### 3. OpenAI API Automation

```
Project Name: openai-api-automation-demo (or your choice)
Framework Preset: Other
Root Directory: openai-api-automation [IMPORTANT: Click Edit → Select folder]
Build Command: [leave empty]
Install Command: pip install -r requirements.txt
Environment Variables:
  - OPENAI_API_KEY (optional - works in mock mode without it)
  - OPENAI_MODEL (optional - defaults to gpt-4o-mini)
  - TELEGRAM_BOT_TOKEN (optional)
  - TELEGRAM_CHAT_ID (optional)
  - EMAIL_ENABLED (optional)
```

**Function Settings** (auto-configured via vercel.json):
- Max Duration: 30s
- Memory: 512MB

**Post-Deploy Test**:
```bash
curl https://your-deployment.vercel.app/health
# Expected: {"status":"healthy","service":"openai-api-automation","ai_mode":"mock",...}

curl https://your-deployment.vercel.app/sample
# Should return JSON with processed inquiry data
```

---

## 🎯 Deployment Steps (Dashboard Method)

### For Each Project:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your repository: `Lt-wei/ai-solutions-portfolio`
4. **CRITICAL**: Click "Edit" next to Root Directory and select the project folder
5. Set Framework Preset to **"Other"**
6. Set Install Command to `pip install -r requirements.txt`
7. Leave Build Command and Output Directory empty
8. Add environment variables if needed (all optional)
9. Click **"Deploy"**
10. Wait ~1-2 minutes for deployment
11. Test the deployment using the URLs above

---

## 📝 Post-Deployment Checklist

After all three are deployed:

### Excel Automation ✓
- [ ] Health endpoint responds
- [ ] Home page loads with UI
- [ ] "Try with Sample Data" button works
- [ ] Excel file downloads successfully
- [ ] Sample data processes correctly (9 → 6 rows after dedup/filter)

### PDF Document AI ✓
- [ ] Health endpoint responds
- [ ] Home page loads with UI
- [ ] "Try with Sample Contracts" button works
- [ ] Extracts data from 3 sample PDFs
- [ ] Excel output downloads successfully
- [ ] Shows contract numbers, amounts, dates

### OpenAI API Automation ✓
- [ ] Health endpoint responds
- [ ] Home page loads with UI
- [ ] "Try Sample Inquiry" button works
- [ ] Shows category, priority, sentiment
- [ ] Database persists inquiries (SQLite in /tmp)
- [ ] Works in demo mode without API key

---

## 🔧 Common Issues

### Issue: "Root Directory not found"
**Solution**: Must click "Edit" button and **select** the folder from dropdown, not just type it.

### Issue: "requirements.txt not found"
**Solution**: Verify Root Directory is set correctly. The requirements.txt must be in the selected folder.

### Issue: Function timeout
**Solution**: Configured in vercel.json. Defaults are sufficient for all three apps.

### Issue: "OPENAI_API_KEY not found" error
**Solution**: This is normal! All apps work without API keys:
- Excel: No API needed
- PDF: Uses regex/heuristic extraction
- OpenAI: Uses mock/rule-based responses

### Issue: SQLite database errors (OpenAI app)
**Solution**: Database recreates on each cold start in /tmp. This is expected for serverless. Data is not persistent across deployments.

---

## 🚨 Important Notes

1. **Root Directory is mandatory** - Each project must be deployed separately
2. **One repo = Three Vercel projects** - Import same repo three times, change Root Directory each time
3. **All work without API keys** - Perfect for portfolio demonstrations
4. **File size limits**: 10MB per upload (configured in apps)
5. **SQLite in /tmp**: OpenAI app database is ephemeral on serverless

---

## 📊 What Each App Does

**Excel Automation**: Clean/dedupe/transform/filter spreadsheet data with configurable rules
- Uses sample: `customers_raw.xlsx` + `rules.json`
- Deduplicates by email, transforms to title case, filters age 18-100
- Output: Processed Excel + JSON report

**PDF Document AI**: Extract structured contract data from PDFs (AI or regex)
- Uses 3 sample contract PDFs
- Extracts: contract number, company, amount, date, parties
- Output: Excel file with all extracted contracts

**OpenAI API Automation**: Process inquiries with AI categorization/priority
- Sample: Enterprise plan inquiry
- Categorizes (billing/support/sales), assigns priority, detects sentiment
- Stores in SQLite, sends notifications (simulated)

---

## ✅ Success Criteria

You're ready when:
1. All three projects deployed to separate Vercel URLs
2. Each health endpoint returns 200 status
3. Sample buttons work and produce downloadable outputs
4. README files updated with live demo URLs (replace `LIVE_DEMO_URL_*` tokens)

---

**Total deployment time**: ~10-15 minutes for all three projects

**Cost**: Free (Vercel free tier is sufficient)
