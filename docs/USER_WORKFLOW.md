# User Workflow Guide

## Overview

The sentiment analysis dashboard features an intuitive, modal-based workflow for running analyses on social media data. This guide walks through the complete user experience.

---

## 🚀 Getting Started

### 1. Launch the Dashboard

```bash
python main.py --mode dashboard
```

Then open your browser to: **http://localhost:5000**

---

## 📊 Running an Analysis

### Step 1: Click "Run Analysis" Button

Located at the top left of the dashboard, this prominent button opens the analysis configuration modal.

### Step 2: Configure Your Analysis

The modal presents two key inputs:

**Keywords to Track**
- Enter topics you want to analyze (e.g., "AI, Python, Climate Change")
- Separate multiple keywords with commas
- Keywords are case-insensitive

**Time Range**
- Choose from predefined ranges:
  - **Last 60 seconds (Demo)** - Perfect for live presentations! 🎬
  - Last 24 hours
  - Last 3 days
  - Last 7 days
  - Last 30 days

Need to update your defaults before running? Click **"Manage Keywords"** on the dashboard to open a dedicated editor—saved keywords auto-fill this dialog next time.

### Step 3: Start Analysis

Click the **"Start Analysis"** button. The modal closes immediately.

### Step 4: Monitor Progress

A status bar appears next to the "Run Analysis" button showing:

1. **Initializing** 🔄
   ```
   Initializing analysis...
   ```

2. **Collecting** 🔄
   ```
   Collecting data from social media platforms...
   ```

3. **Complete** ✅
   ```
   Analysis complete! Dashboard updated.
   ```

If an error occurs, you'll see:
```
❌ Analysis failed. Please try again.
```

### Step 5: View Results

The dashboard automatically refreshes when analysis completes:

- **Keyword Cards** show sentiment breakdown for each keyword
- **Charts** update with new data
- **Stats** reflect the analyzed posts

---

## 🎯 Keyword Cards Feature

After analysis completes, you'll see cards for each keyword:

```
┌─────────────────────┐
│      Keyword        │
│    "AI"             │
│                     │
│  😊 45%  😐 30%  ☹️ 25%  │
│  [████░░░░]        │
│                     │
│  156 posts analyzed │
└─────────────────────┘
```

**Click any card** to filter the entire dashboard to show only that keyword's data.

---

## 💡 Best Practices

### Keyword Selection
- ✅ **Be specific**: "Climate Change" vs "Climate"
- ✅ **Use 2-5 keywords**: Focused analysis is better
- ✅ **Mix topics**: Compare sentiment across different subjects

### Time Range Selection
- 📅 **60 seconds**: Live demos and presentations (gets most recent posts)
- 📅 **24 hours**: Real-time trends, breaking news
- 📅 **3-7 days**: Weekly sentiment shifts
- 📅 **30 days**: Long-term trend analysis

### Analysis Frequency
- 🔄 Run analysis when you need fresh data
- 🔄 Compare different time periods
- 🔄 Track sentiment changes over time

### 🎬 For Live Presentations
- Use the **60 seconds** option for quick, impressive demos
- Choose trending keywords with high activity
- Start analysis, explain the system while it runs (~30-45s)
- Dashboard auto-refreshes when complete - perfect timing!

---

## 🛠️ Troubleshooting

### Analysis Stuck?

**Check status message** - It should update every 2 seconds

**Refresh the page** - If stuck for >2 minutes

**Check browser console** - Press F12 for error details

### No Data Collected?

**Verify API credentials** - Check your `.env` file

**Broaden keywords** - Try more general terms

**Extend time range** - Older posts might have more data

### Dashboard Not Updating?

**Wait for completion** - Analysis can take 30-60 seconds

**Manual refresh** - Click the "Refresh" button

**Check network tab** - Ensure API calls succeed

---

## 📈 Advanced Usage

### Comparing Multiple Keywords

1. Run analysis with keywords: "Python, JavaScript, Rust"
2. View individual keyword cards
3. Click each card to compare sentiment

### Time-Series Analysis

1. Run analysis for "Last 7 days"
2. Note the results
3. Run again after a few days
4. Compare trend changes

### Platform-Specific Insights

Use the platform filter in the dashboard to see:
- Twitter vs Reddit sentiment differences
- Platform-specific language patterns
- Engagement variations

---

## 🔐 Privacy & Rate Limits

- **No data stored permanently** unless you configure it
- **Rate limits respected** - Analysis may pause if limits hit
- **API keys required** - Configure in `.env` file

---

## 🎨 UI Features

### Status Indicators

- 🔵 **Blue spinner**: Analysis running
- 🟢 **Green checkmark**: Success
- 🔴 **Red X**: Error

### Animations

- **Modal slide-in**: Smooth appearance
- **Progress fade**: Status updates
- **Card hover**: Interactive feedback

### Responsive Design

- Works on desktop, tablet, and mobile
- Charts scale automatically
- Modal adapts to screen size

---

## 📞 Support

For issues or questions:

1. Check the `README.md` for setup instructions
2. Review `API_DOCUMENTATION.md` for technical details
3. Check logs in the `logs/` directory
4. Open an issue on GitHub

---

## 🎉 Happy Analyzing!

The new workflow makes sentiment analysis **simple, intuitive, and powerful**. Run analyses on-demand, track multiple keywords, and visualize sentiment trends with ease.
