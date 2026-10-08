# 🚀 Deployment Guide

Complete guide for deploying all three projects to Vercel.

## Prerequisites

- [Vercel Account](https://vercel.com/signup) (free tier is sufficient)
- [Vercel CLI](https://vercel.com/cli) installed (optional, can use dashboard)
- GitHub repository connected to Vercel

## Quick Deploy Summary

Each project deploys as a **separate Vercel project** with the **Root Directory** setting pointing to its subfolder.

| Project | Root Directory | Required Env Vars | Max Duration | Memory |
|---------|---------------|-------------------|--------------|---------|
| Excel Automation | `excel-automation` | None | 30s | 512MB |
| PDF Document AI | `pdf-document-ai` | None | 30s | 1024MB |
| OpenAI API Automation | `openai-api-automation` | None (optional: `OPENAI_API_KEY`) | 30s | 512MB |

## Method 1: Vercel Dashboard (Recommended)

### Step 1: Create First Project (Excel Automation)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. **Important Settings:**
   - **Project Name**: `excel-automation-demo` (or your choice)
   - **Framework Preset**: Other
   - **Root Directory**: Click "Edit" and select `excel-automation`
   - **Build Command**: (leave empty)
   - **Install Command**: `pip install -r requirements.txt`
   - **Output Directory**: (leave empty)
5. Click **"Deploy"**
6. Wait for deployment to complete
7. Copy the production URL (e.g., `https://excel-automation-demo.vercel.app`)

### Step 2: Create Second Project (PDF Document AI)

1. From Vercel Dashboard, click **"Add New..."** → **"Project"**
2. Select **same repository** again
3. **Important Settings:**
   - **Project Name**: `pdf-document-ai-demo`
   - **Framework Preset**: Other
   - **Root Directory**: Click "Edit" and select `pdf-document-ai`
   - **Build Command**: (leave empty)
   - **Install Command**: `pip install -r requirements.txt`
4. Click **"Deploy"**
5. Copy the production URL

### Step 3: Create Third Project (OpenAI API Automation)

1. From Vercel Dashboard, click **"Add New..."** → **"Project"**
2. Select **same repository** again
3. **Important Settings:**
   - **Project Name**: `openai-api-automation-demo`
   - **Framework Preset**: Other
   - **Root Directory**: Click "Edit" and select `openai-api-automation`
   - **Build Command**: (leave empty)
   - **Install Command**: `pip install -r requirements.txt`
   - **Environment Variables** (optional):
     - Key: `OPENAI_API_KEY`
     - Value: `sk-...` (your OpenAI API key - **optional**, works without it)
4. Click **"Deploy"**
5. Copy the production URL

## Method 2: Vercel CLI

```bash
# Install Vercel CLI (if not already installed)
npm i -g vercel

# Login to Vercel
vercel login

# Deploy Excel Automation
cd excel-automation
vercel --prod
# Follow prompts, set root directory to current directory

# Deploy PDF Document AI
cd ../pdf-document-ai
vercel --prod

# Deploy OpenAI API Automation
cd ../openai-api-automation
vercel --prod
# Optionally add OPENAI_API_KEY environment variable later via dashboard
```

## Post-Deployment Steps

### 1. Update README Files

After all three projects are deployed, update the live demo URLs:

```bash
# Replace placeholders in root README.md
LIVE_DEMO_URL_EXCEL="https://your-excel-deployment.vercel.app"
LIVE_DEMO_URL_PDF="https://your-pdf-deployment.vercel.app"
LIVE_DEMO_URL_API="https://your-api-deployment.vercel.app"

# Update in:
# - README.md (root)
# - excel-automation/README.md
# - pdf-document-ai/README.md
# - openai-api-automation/README.md
```

### 2. Test Each Deployment

Visit each URL and test:

✅ **Excel Automation:**
- [ ] Page loads correctly
- [ ] Click "Try with Sample Data" button
- [ ] Excel file downloads successfully
- [ ] File opens in Excel/Google Sheets with formatting

✅ **PDF Document AI:**
- [ ] Page loads correctly
- [ ] Click "Try with Sample Invoice" button
- [ ] Results display with extracted data
- [ ] Statistics show correct counts

✅ **OpenAI API Automation:**
- [ ] Page loads correctly
- [ ] Sample data buttons load text
- [ ] "Process Text" button works
- [ ] Results display with demo mode notice
- [ ] All task types work (summarize, sentiment, keywords, translate)

### 3. Verify Serverless Function Logs

In Vercel Dashboard for each project:
1. Go to **Deployments** tab
2. Click on latest deployment
3. Check **Functions** tab
4. Verify no errors in logs

### 4. Add Custom Domains (Optional)

For professional URLs:

1. Go to project **Settings** → **Domains**
2. Add your custom domain (e.g., `excel.yourdomain.com`)
3. Configure DNS records as instructed
4. Update README URLs

## Common Issues & Solutions

### Issue: "Module not found" error

**Solution:** Verify `requirements.txt` is in the root directory of each project folder.

### Issue: Function timeout

**Solution:** Each project has `vercel.json` with `maxDuration: 30`. This should be sufficient. If needed, increase to 60 for larger files.

### Issue: "File too large" error

**Solution:** This is expected for files over the limits (5MB for Excel, 10MB for PDF). The UI warns users about size limits.

### Issue: OpenAI API errors

**Solution:** 
- If no `OPENAI_API_KEY` is set, app runs in demo mode (this is intentional)
- If key is set but invalid, check the key in Vercel project settings
- Demo mode is free and perfect for portfolio demonstrations

### Issue: Excel file won't download

**Solution:** 
- Check browser console for errors
- Verify `/sample` endpoint returns 200 status
- Test with: `curl https://your-deployment.vercel.app/sample -o test.xlsx`

### Issue: PDF sample generation fails

**Solution:** 
- Check function logs for reportlab errors
- Verify function has 1024MB memory (set in vercel.json)
- Sample PDF is generated on-the-fly using reportlab

## Performance Optimization

### Cold Starts
- First request after inactivity may take 2-3 seconds
- Subsequent requests are instant
- This is normal for serverless functions

### Memory Settings
- Excel Automation: 512MB (sufficient)
- PDF Document AI: 1024MB (needed for reportlab)
- OpenAI API Automation: 512MB (sufficient)

### Caching
- Static assets (HTML/CSS/JS) are automatically cached at edge
- API responses are not cached (desired for dynamic content)

## Monitoring

### Check Health Endpoints

```bash
curl https://your-excel-deployment.vercel.app/health
curl https://your-pdf-deployment.vercel.app/health
curl https://your-api-deployment.vercel.app/health
```

All should return `{"status": "healthy", ...}`

### View Analytics

In Vercel Dashboard:
1. Go to **Analytics** tab
2. Monitor request counts
3. Check function execution times
4. View error rates

## Security Notes

- ✅ No sensitive data is stored
- ✅ All file processing happens in `/tmp` (cleared after request)
- ✅ Upload size limits prevent abuse
- ✅ No database or persistent storage
- ✅ OPENAI_API_KEY (if used) is never exposed to client

## Cost Considerations

### Vercel Free Tier Includes:
- 100GB bandwidth/month
- 100 hours serverless function execution
- Unlimited deployments

### Expected Usage:
- Each demo request: ~0.5-2 seconds of function time
- File downloads: ~50KB-500KB bandwidth
- Free tier is more than sufficient for portfolio demonstrations

### OpenAI API Costs (if enabled):
- GPT-4o-mini: ~$0.15 per 1M tokens
- Each request: ~$0.0001-0.001
- Demo mode is free and recommended for portfolio

## Troubleshooting Checklist

- [ ] Root Directory is correctly set for each project
- [ ] `requirements.txt` exists in each project folder
- [ ] `app.py` exports FastAPI `app` variable
- [ ] `vercel.json` is properly formatted
- [ ] Environment variables (if any) are set in Vercel dashboard
- [ ] Deployment logs show no errors
- [ ] Health endpoints return 200 status
- [ ] Sample data buttons work without errors

## Support Resources

- [Vercel Python Documentation](https://vercel.com/docs/functions/runtimes/python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vercel Deployment Logs](https://vercel.com/docs/observability/logging)

## Next Steps After Deployment

1. ✅ Test all three live demos thoroughly
2. ✅ Take screenshots and update docs/ folders
3. ✅ Update all README files with live URLs
4. ✅ Add to Upwork portfolio with live demo links
5. ✅ Share on LinkedIn/Twitter with demos
6. ✅ Add to resume with verifiable live projects

---

**Ready to deploy?** Start with Method 1 (Dashboard) - it's the most straightforward!
