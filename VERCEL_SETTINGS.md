# ⚙️ Vercel Project Settings Reference

Quick copy-paste reference for creating each project in Vercel Dashboard.

---

## 📊 Project 1: Excel Automation

### Project Settings
```
Project Name: excel-automation-demo
Framework Preset: Other
Root Directory: excel-automation
```

### Build & Development Settings
```
Build Command: [leave empty]
Output Directory: [leave empty]
Install Command: pip install -r requirements.txt
Development Command: python3 app.py
```

### Environment Variables
```
None required ✓
```

### Function Settings (auto-configured via vercel.json)
```
Max Duration: 30 seconds
Memory: 512 MB
Region: Auto
```

### Post-Deployment Test
```bash
curl https://your-deployment.vercel.app/health
# Expected: {"status":"healthy","service":"excel-automation"}

curl https://your-deployment.vercel.app/sample -o test.xlsx
# Expected: Downloads test.xlsx file
```

---

## 📄 Project 2: PDF Document AI

### Project Settings
```
Project Name: pdf-document-ai-demo
Framework Preset: Other
Root Directory: pdf-document-ai
```

### Build & Development Settings
```
Build Command: [leave empty]
Output Directory: [leave empty]
Install Command: pip install -r requirements.txt
Development Command: python3 app.py
```

### Environment Variables
```
None required ✓
```

### Function Settings (auto-configured via vercel.json)
```
Max Duration: 30 seconds
Memory: 1024 MB (higher for PDF processing + reportlab)
Region: Auto
```

### Post-Deployment Test
```bash
curl https://your-deployment.vercel.app/health
# Expected: {"status":"healthy","service":"pdf-document-ai"}

curl https://your-deployment.vercel.app/sample
# Expected: JSON with extracted PDF data
```

---

## 🤖 Project 3: OpenAI API Automation

### Project Settings
```
Project Name: openai-api-automation-demo
Framework Preset: Other
Root Directory: openai-api-automation
```

### Build & Development Settings
```
Build Command: [leave empty]
Output Directory: [leave empty]
Install Command: pip install -r requirements.txt
Development Command: python3 app.py
```

### Environment Variables
```
OPENAI_API_KEY (optional)
├─ Value: sk-your-key-here
├─ Environments: Production, Preview, Development
└─ Note: If omitted, runs in demo mode (free, no API calls)
```

### Function Settings (auto-configured via vercel.json)
```
Max Duration: 30 seconds
Memory: 512 MB
Region: Auto
```

### Post-Deployment Test
```bash
curl https://your-deployment.vercel.app/health
# Expected: {"status":"healthy","service":"openai-api-automation","api_mode":"demo"}

curl -X POST https://your-deployment.vercel.app/process \
  -H "Content-Type: application/json" \
  -d '{"text":"Great product!","task":"sentiment"}'
# Expected: JSON with sentiment analysis
```

---

## 🔍 Verification Checklist

After deploying all three projects:

### Excel Automation
- [ ] Home page loads with UI
- [ ] "Try with Sample Data" downloads Excel file
- [ ] Excel file has proper formatting (colors, borders, widths)
- [ ] Health endpoint returns 200

### PDF Document AI
- [ ] Home page loads with UI
- [ ] "Try with Sample Invoice" shows extracted data
- [ ] Results display emails, phones, dates, amounts
- [ ] Health endpoint returns 200

### OpenAI API Automation
- [ ] Home page loads with UI
- [ ] Sample buttons load text
- [ ] All 4 tasks work (summarize, sentiment, keywords, translate)
- [ ] Demo mode indicator visible
- [ ] Health endpoint returns 200

---

## 📝 Common Configurations

### All Projects Share:
- **Runtime**: Python 3.12
- **Region**: Automatic (closest to users)
- **Auto-assign Domains**: Yes
- **Deployment Protection**: None (public demos)
- **Analytics**: Enabled (recommended)

### Pricing Tier Required:
- **Free Tier**: Sufficient for all projects
- **No credit card required** for deployment

### Estimated Monthly Usage (Free Tier):
```
Bandwidth: <1GB (well under 100GB limit)
Function Executions: <10,000 (well under limits)
Build Minutes: <10 minutes (well under limits)
```

---

## 🚨 Troubleshooting

### If deployment fails:

1. **Check Root Directory**
   - Must exactly match folder name: `excel-automation`, `pdf-document-ai`, `openai-api-automation`
   - Case-sensitive

2. **Verify requirements.txt**
   - Must be in project root (not repo root)
   - Check for typos in package names

3. **Check vercel.json**
   - Must be valid JSON
   - In same directory as app.py

4. **Review Function Logs**
   - Deployments → Click latest → Functions tab
   - Look for Python import errors

### If function times out:

1. Increase `maxDuration` in vercel.json
2. For PDF project, ensure `memory: 1024` is set
3. Check for infinite loops in code

### If environment variable not working:

1. Verify spelling matches exactly
2. Ensure selected for correct environment (Production/Preview)
3. Redeploy after adding/changing env vars

---

## 🎯 Post-Deployment Actions

1. **Update READMEs** with live URLs
   ```bash
   # Replace in all README.md files:
   LIVE_DEMO_URL_EXCEL → https://excel-automation-demo.vercel.app
   LIVE_DEMO_URL_PDF → https://pdf-document-ai-demo.vercel.app
   LIVE_DEMO_URL_API → https://openai-api-automation-demo.vercel.app
   ```

2. **Take Screenshots**
   - Visit each live URL
   - Capture interface and results
   - Add to docs/ folders
   - Commit and push

3. **Test End-to-End**
   - Use each demo as a client would
   - Verify downloads work
   - Check mobile responsiveness
   - Test on different browsers

4. **Share**
   - Add to Upwork portfolio
   - Share on LinkedIn
   - Include in resume
   - Send to potential clients

---

**Ready to deploy?** Follow DEPLOYMENT_GUIDE.md for step-by-step instructions!
