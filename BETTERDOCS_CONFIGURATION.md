# BetterDocs Configuration Guide for Tickertronix Documentation Hub

## Overview
BetterDocs (version 4.2.1) is currently **active** on tickertronix.com and powers the `/docs/` documentation hub. This guide provides a comprehensive review of the current setup and recommendations for organizing technical documentation to support the DIY maker hub transformation.

---

## Current State Analysis

### Docs Page
- **Page ID:** 19
- **URL:** `/docs/`
- **Shortcode:** `[betterdocs]` (active)
- **Status:** Published and functional

### Existing Documentation
**Total Docs:** 11 documents found

#### Published Docs (with duplicates identified):
1. **Getting Started** (IDs: 48, 60) - Duplicate ⚠️
2. **DIY Guides: Basics** (IDs: 49, 61) - Duplicate ⚠️
3. **API Keys: Setup** (IDs: 50, 62) - Duplicate ⚠️
4. **Troubleshooting: Common Issues** (IDs: 51, 63) - Duplicate ⚠️
5. **Changelog** (IDs: 52, 64) - Duplicate ⚠️
6. **Test Doc** (ID: 58) - Should be deleted

#### Issues Found:
- ❌ **Duplicate content**: Each doc appears twice with different IDs
- ❌ **Placeholder content**: Docs contain minimal stub content
- ❌ **Test doc present**: ID 58 should be removed
- ❌ **No category organization**: Docs don't appear to be organized into categories
- ❌ **Missing platform-specific docs**: No Pi Hub, CYD, or Matrix Portal specific guides
- ❌ **Old focus**: Content seems geared toward app/service, not DIY hardware hub

---

## Step 1: Clean Up Existing Docs

### Delete Duplicate Docs
Navigate to **WordPress Admin → Docs → All Docs**

**Delete these duplicate IDs:**
- ID 60 (Getting Started - duplicate)
- ID 61 (DIY Guides: Basics - duplicate)
- ID 62 (API Keys: Setup - duplicate)
- ID 63 (Troubleshooting: Common Issues - duplicate)
- ID 64 (Changelog - duplicate)
- ID 58 (Test Doc - should be removed)

**Keep these original IDs for updating:**
- ID 48 (Getting Started)
- ID 49 (DIY Guides: Basics)
- ID 50 (API Keys: Setup)
- ID 51 (Troubleshooting: Common Issues)
- ID 52 (Changelog)

---

## Step 2: Create Doc Categories

Navigate to **WordPress Admin → Docs → Doc Categories**

### Recommended Category Structure:

#### 1. 🚀 Getting Started (Category)
**Slug:** `getting-started`
**Description:** "New to Tickertronix? Start here to understand the hub-client architecture and choose your first build."
**Order:** 1

**Docs in this category:**
- Welcome to Tickertronix DIY Hub
- Understanding the Hub-Client Architecture
- Choosing Your Hardware
- Required Tools & Skills
- Alpaca Markets API Setup (Free Tier)

---

#### 2. 🍓 Raspberry Pi Hub (Category)
**Slug:** `raspberry-pi-hub`
**Description:** "Complete setup guide for the required Raspberry Pi Price Hub - the central server for all your displays."
**Order:** 2

**Docs in this category:**
- **Hardware Requirements**
  - Pi Zero 2 W vs Pi 4: Which to Choose?
  - Recommended SD Cards and Power Supplies
  - Optional Cooling Solutions

- **Installation & Setup**
  - Quick Install (5-Minute Script)
  - Manual Installation (Step-by-Step)
  - Network Configuration (WiFi vs Ethernet)
  - mDNS Setup (tickertronixhub.local)

- **Configuration**
  - Configuring Alpaca API Integration
  - Adding Twelve Data for Forex (Optional)
  - Setting Up Tracked Tickers
  - Environment Variables Reference

- **API Reference**
  - Endpoints Overview (/prices, /health, /status)
  - Response Format Specifications
  - Rate Limiting and Caching
  - Error Codes and Troubleshooting

- **Maintenance**
  - Updating the Hub Software
  - Backup and Restore
  - Performance Monitoring
  - Log Analysis

---

#### 3. 📺 CYD Ticker (Category)
**Slug:** `cyd-ticker`
**Description:** "Build guide for the $15-25 ESP32 touchscreen display ticker."
**Order:** 3

**Docs in this category:**
- **Hardware**
  - Parts List and Where to Buy
  - Soldering Guide (if needed)
  - 3D Printable Case Assembly
  - Troubleshooting Hardware Issues

- **Firmware**
  - Arduino IDE Setup
  - Installing Required Libraries
  - Flashing the Firmware
  - OTA Updates

- **Configuration**
  - WiFi Provisioning (Web Portal)
  - Connecting to Pi Hub
  - Display Settings (Brightness, Rotation)
  - Customizing Ticker Selection

- **Advanced**
  - Multi-Ticker Display Layouts
  - Touchscreen Calibration
  - Custom Fonts and Themes
  - Power Management

---

#### 4. 🔲 Matrix Portal (Category)
**Slug:** `matrix-portal`
**Description:** "CircuitPython-powered scrolling LED matrix display."
**Order:** 4

**Docs in this category:**
- **Hardware**
  - Matrix Portal S3 vs Original
  - LED Panel Options (32x32, 64x32, dual-panel)
  - Power Requirements and PSU Selection
  - 3D Printable Mounts

- **Firmware**
  - CircuitPython Installation
  - Copying Firmware to CIRCUITPY Drive
  - Required Libraries
  - Firmware Updates

- **Configuration**
  - WiFi Provisioning (TickerSetup AP)
  - Hub Connection Setup
  - Scroll Speed and Font Selection
  - Display Brightness (Single vs Multi-Panel)

- **Advanced**
  - Dual-Panel Configuration
  - Custom Fonts (8x16, 16x32)
  - Enabling Forex Display
  - Low-Power Mode

---

#### 5. 🔧 Advanced Topics (Category)
**Slug:** `advanced`
**Description:** "Advanced configurations, customizations, and integrations."
**Order:** 5

**Docs in this category:**
- Multi-Hub Deployments (Multiple Locations)
- Custom API Integrations
- Building Your Own Display Client
- Performance Optimization
- Security Best Practices
- Docker Deployment (Pi Hub)
- Kubernetes Cluster Setup (Advanced)

---

#### 6. 🛠️ Troubleshooting (Category)
**Slug:** `troubleshooting`
**Description:** "Common issues and how to fix them."
**Order:** 6

**Docs in this category:**
- **Pi Hub Issues**
  - Service Won't Start
  - API Returns No Data
  - High CPU/Memory Usage
  - Network Discovery Not Working

- **CYD Issues**
  - Display Not Turning On
  - WiFi Connection Failures
  - Touchscreen Not Responding
  - Flash Errors

- **Matrix Portal Issues**
  - LED Panel Not Lighting
  - Scrolling Lag or Flicker
  - CircuitPython Errors
  - Power Supply Problems

- **General Issues**
  - API Key Rate Limits
  - Network Firewall Blocking
  - DNS/mDNS Not Resolving
  - Slow Data Updates

---

#### 7. 📚 API Reference (Category)
**Slug:** `api-reference`
**Description:** "Complete API documentation for developers."
**Order:** 7

**Docs in this category:**
- Hub API Endpoints
- Authentication (if added later)
- WebSocket Support (future)
- Rate Limits and Quotas
- Response Schemas
- Error Handling
- Pagination
- Webhooks (future)

---

#### 8. 🎓 Tutorials (Category)
**Slug:** `tutorials`
**Description:** "Step-by-step tutorials for specific projects."
**Order:** 8

**Docs in this category:**
- Building Your First CYD Ticker (Complete Walkthrough)
- Setting Up a 3-Display Home Office Setup
- Creating a Custom Ticker Layout
- Migrating from Cloud Service to Local Hub
- Adding Custom Market Data Sources
- Building a Wall-Mounted Matrix Display

---

#### 9. 🤝 Contributing (Category)
**Slug:** `contributing`
**Description:** "Contribute to Tickertronix open-source project."
**Order:** 9

**Docs in this category:**
- Code of Conduct
- Development Setup
- Submitting Pull Requests
- Reporting Bugs
- Feature Requests
- Documentation Guidelines
- Testing Procedures

---

#### 10. 📋 Changelog (Category)
**Slug:** `changelog`
**Description:** "Version history and release notes."
**Order:** 10

**Docs in this category:**
- Hub Firmware Changelog
- CYD Firmware Changelog
- Matrix Portal Firmware Changelog
- Website Updates
- Breaking Changes

---

## Step 3: Configure BetterDocs Settings

Navigate to **WordPress Admin → BetterDocs → Settings**

### General Settings:

```
Documentation Page: Docs (ID 19)
Docs Per Page: 10
Archive Order By: Title
Archive Order: ASC
Enable Live Search: ✅ Yes
Enable Table of Contents: ✅ Yes
Enable Breadcrumbs: ✅ Yes
Enable Print Button: ✅ Yes
Enable Social Share: ❌ No (focus on GitHub instead)
```

### Layout Settings:

```
Layout Type: Docs Page Layout 1 (Grid with sidebar)
Sidebar Position: Right
Category Icon: Custom icons (upload for each category)
Category Description: Show
Related Docs: Show (max 5)
Docs Feedback: Enable (👍 👎 buttons)
```

### Customization (Match Dark Theme):

```css
/* Primary Color */
--betterdocs-primary-color: #4A3AFD;

/* Background */
--betterdocs-bg-color: #00031c;
--betterdocs-card-bg: #0a0f2c;

/* Text */
--betterdocs-text-color: #ffffff;
--betterdocs-heading-color: #ffffff;

/* Links */
--betterdocs-link-color: #4A3AFD;
--betterdocs-link-hover: #6B5BFF;

/* Search */
--betterdocs-search-bg: #0a0f2c;
--betterdocs-search-border: #4A3AFD;

/* Categories */
--betterdocs-category-bg: #0a0f2c;
--betterdocs-category-border: #4A3AFD;
--betterdocs-category-hover: #1a1f4c;

/* Code Blocks */
--betterdocs-code-bg: #1a1f4c;
--betterdocs-code-border: #4A3AFD;
```

### Search Settings:

```
Enable Instant Search: ✅ Yes
Search Placeholder: "Search documentation..."
Search Category Filter: ✅ Enable
Popular Search Keywords:
  - Raspberry Pi setup
  - CYD ticker
  - Matrix Portal
  - API keys
  - WiFi configuration
  - Troubleshooting
```

### Advanced Settings:

```
Enable Analytics: ✅ Yes (track popular docs)
Enable Comments: ❌ No (use forum for questions)
Enable Reactions: ✅ Yes (helpful/not helpful)
Enable TOC Sticky: ✅ Yes
Breadcrumb Separator: "/"
```

---

## Step 4: Update Existing Docs

Update the 5 docs we kept (IDs 48, 49, 50, 51, 52) with comprehensive content aligned with the new DIY hub focus.

### Template for Each Doc:

```markdown
# [Doc Title]

## Overview
Brief 1-2 sentence summary of what this doc covers.

## Prerequisites
- Required hardware/software
- Prior knowledge needed
- Estimated time to complete

## Step-by-Step Guide

### Step 1: [First Major Step]
Detailed instructions with:
- Screenshots where helpful
- Code blocks with syntax highlighting
- Warning/info callouts for important notes

### Step 2: [Second Major Step]
Continue with clear, numbered steps...

## Troubleshooting
Common issues users might encounter:

**Issue:** Description of problem
**Cause:** Why it happens
**Solution:** How to fix it

## Next Steps
- Link to related docs
- Suggest logical next action
- Point to community resources

## See Also
- [Related Doc 1](link)
- [Related Doc 2](link)
- [External Resource](link)
```

### Suggested Rewrites:

#### ID 48: Getting Started → "Welcome to Tickertronix DIY Hub"
- Explain hub-client architecture
- Show all three platforms with clear "Start with Pi Hub" guidance
- Link to hardware comparison
- Overview of what users will build
- Community links (GitHub, forum)

#### ID 49: DIY Guides: Basics → "Understanding the Hub-Client Architecture"
- Deep dive into how the system works
- Data flow diagram (API → Hub → Display)
- Local vs cloud comparison
- Why this architecture matters
- Security and privacy benefits

#### ID 50: API Keys: Setup → "Alpaca Markets API Setup (Free Tier)"
- Step-by-step Alpaca account creation
- Where to find API keys
- Rate limits explained (15 req/min)
- How to add keys to Pi Hub .env file
- Testing API connection
- Optional: Twelve Data for forex

#### ID 51: Troubleshooting: Common Issues → Keep as general troubleshooting index
- Reorganize as landing page for troubleshooting category
- Link to platform-specific troubleshooting docs
- Quick diagnostic flowchart
- When to ask for help on forum

#### ID 52: Changelog → Update with recent changes
- Hub firmware versions
- Breaking changes
- Migration guides
- Deprecated features

---

## Step 5: Create Priority Docs

These docs should be created first to support the new homepage and build pages:

### Highest Priority (Create This Week):

1. **Raspberry Pi Hub: Quick Install**
   - Category: Raspberry Pi Hub > Installation & Setup
   - Content: Expand on `/mnt/c/users/timot/tickertronix_complete/tickertronix-price-hub/docs/PI_DEPLOY.md`
   - Include: Hardware requirements, script usage, network config, testing

2. **CYD Ticker: Complete Build Guide**
   - Category: CYD Ticker > Hardware
   - Content: Parts list, assembly, flashing, first boot
   - Link to: 3D case files, firmware download, WiFi setup

3. **Matrix Portal: Getting Started**
   - Category: Matrix Portal > Hardware
   - Content: Based on `/mnt/c/users/timot/tickertronix_complete/tickertronix-price-hub/matrix-portal-scroll/README.md`
   - Include: CircuitPython setup, provisioning, troubleshooting

4. **Hardware Comparison Guide**
   - Category: Getting Started
   - Content: Expand on Hardware Comparison page (ID 275)
   - Help users choose the right hardware

5. **Alpaca API Configuration**
   - Category: Raspberry Pi Hub > Configuration
   - Content: Detailed API key setup, rate limits, testing

### Medium Priority (Create This Month):

6. API Endpoint Reference
7. WiFi Provisioning for All Platforms
8. 3D Printing Guide (Print Settings, Materials)
9. Firmware Update Procedures
10. Multi-Display Setup Tutorial

### Lower Priority (Create As Needed):

11. Advanced customizations
12. Performance tuning
13. Docker deployment
14. Custom firmware development

---

## Step 6: Add Doc Template for Contributors

Create a "New Doc Template" file that contributors can copy:

Navigate to **WordPress Admin → Docs → Add New**

**Title:** "_TEMPLATE - Copy This for New Docs"
**Category:** Contributing
**Status:** Draft (don't publish)

**Content:**
```markdown
# [Doc Title - Be Specific and Descriptive]

## Overview
[One sentence describing what this doc teaches]

## What You'll Learn
- Bullet point 1
- Bullet point 2
- Bullet point 3

## Prerequisites
- [ ] Raspberry Pi Hub installed and running
- [ ] Basic familiarity with [relevant topic]
- [ ] [Hardware/software requirement]

**Time to Complete:** ~XX minutes

---

## Step 1: [First Major Section]

Brief introduction to this step.

### Substep 1.1
Detailed instructions...

```bash
# Code example with syntax highlighting
sudo systemctl status tickertronixhub
```

**Expected Output:**
```
● tickertronixhub.service - Tickertronix Hub Service
   Loaded: loaded
   Active: active (running)
```

### Substep 1.2
Continue with clear steps...

> ⚠️ **Warning:** Important callout for potential issues
> 💡 **Tip:** Helpful hint for better results
> ✅ **Success:** How to verify this step worked

---

## Step 2: [Second Major Section]

Continue with numbered sections...

---

## Troubleshooting

### Issue: [Common Problem]
**Symptoms:** What the user sees
**Cause:** Why it happens
**Solution:**
1. Step to fix
2. Verification step

---

## Next Steps

Now that you've completed [this task], you can:
- [Related task 1](link to doc)
- [Related task 2](link to doc)
- [Advanced topic](link to doc)

---

## See Also

- [Related Doc 1](link)
- [Related Doc 2](link)
- [GitHub Repository](link)
- [Community Forum](link)

---

## Feedback

Was this doc helpful? Let us know with a 👍 or 👎 below, or discuss on our [forum](link).
```

---

## Step 7: Enable Doc Feedback and Analytics

### Feedback Widget:
Navigate to **BetterDocs → Settings → Feedback**

```
Enable Feedback: ✅ Yes
Feedback Type: Emoji reactions + Text
Show "Was this helpful?": ✅ Yes
Collect Email (Optional): ❌ No
Feedback Goes To: Admin email
Auto-Improve: Use feedback to prioritize doc updates
```

### Analytics Integration:

If using Google Analytics or Matomo:

```javascript
// Track doc views
gtag('event', 'doc_view', {
  'event_category': 'Documentation',
  'event_label': document.title,
  'value': 1
});

// Track search queries
gtag('event', 'doc_search', {
  'event_category': 'Documentation',
  'event_label': searchQuery,
  'value': 1
});

// Track helpful/not helpful clicks
gtag('event', 'doc_feedback', {
  'event_category': 'Documentation',
  'event_label': document.title,
  'value': isHelpful ? 1 : 0
});
```

### Key Metrics to Track:
- Most viewed docs
- Most searched keywords
- Docs with lowest "helpful" ratings (need improvement)
- Average time on doc pages
- Bounce rate from docs
- Conversion: docs → forum posts (indicates confusion)

---

## Step 8: Integration with Main Site

### Add Doc Shortcuts to Homepage

Update homepage (ID 14) to include quick links to popular docs:

```html
<section class="quick-docs">
  <h2>📚 Quick Start Guides</h2>
  <div class="doc-cards">
    <a href="/docs/raspberry-pi-hub/quick-install/" class="doc-card">
      <span class="icon">🍓</span>
      <h3>Pi Hub Setup</h3>
      <p>5-minute install</p>
    </a>
    <a href="/docs/cyd-ticker/complete-build/" class="doc-card">
      <span class="icon">📺</span>
      <h3>Build CYD Ticker</h3>
      <p>$20 ESP32 display</p>
    </a>
    <a href="/docs/matrix-portal/getting-started/" class="doc-card">
      <span class="icon">🔲</span>
      <h3>Matrix Portal</h3>
      <p>LED scrolling display</p>
    </a>
  </div>
</section>
```

### Add Search Widget to Header

```html
<!-- BetterDocs Live Search -->
<div class="header-doc-search">
  [betterdocs_search_form placeholder="Search docs..." category_filter="true"]
</div>
```

### Link from Build Pages

Ensure all build guide pages (CYD, Matrix Portal, Pi Hub pages) link prominently to their respective doc categories:

```html
<p>📚 <strong>Need help?</strong> See the complete <a href="/docs/raspberry-pi-hub/">Pi Hub documentation</a> for detailed setup guides and troubleshooting.</p>
```

---

## Step 9: Community Integration

### Link Docs to Forum Categories

Create parallel forum categories (if using bbPress or similar):

- Getting Started Help
- Pi Hub Support
- CYD Ticker Support
- Matrix Portal Support
- General Discussion
- Show Your Build

Add "Ask in Forum" buttons to each doc:

```html
<div class="doc-footer">
  <a href="/forum/pi-hub-support/" class="button">💬 Ask Questions in Forum</a>
  <a href="https://github.com/yourusername/tickertronix/issues" class="button">🐛 Report Bug on GitHub</a>
</div>
```

---

## Step 10: Maintenance Plan

### Weekly:
- Review doc feedback (helpful/not helpful ratings)
- Answer questions in doc comments (if enabled)
- Monitor most-searched keywords to identify missing docs

### Monthly:
- Update docs based on firmware releases
- Add new docs for frequently asked forum questions
- Review analytics to identify poorly performing docs
- Clean up outdated content

### Quarterly:
- Audit all docs for accuracy
- Update screenshots and code examples
- Reorganize categories if needed
- Survey users about doc quality

---

## Shortcodes Reference

### Display All Docs (Main Page):
```
[betterdocs]
```

### Display Specific Category:
```
[betterdocs category_slug="raspberry-pi-hub"]
```

### Search Form:
```
[betterdocs_search_form placeholder="Search..." category_filter="true"]
```

### Popular Docs Widget:
```
[betterdocs_popular_docs title="Popular Guides" posts="5"]
```

### Category Grid:
```
[betterdocs_category_grid number="10" masonry="true"]
```

### Single Doc Table of Contents:
```
[betterdocs_toc]
```

---

## Next Steps

1. ✅ Clean up duplicate docs (delete IDs 58, 60-64)
2. ✅ Create 10 doc categories with descriptions
3. ✅ Configure BetterDocs settings (colors, layout, search)
4. ✅ Update 5 existing docs with comprehensive content
5. ✅ Create 5 highest-priority new docs
6. ✅ Add doc search to site header
7. ✅ Link docs from homepage and build pages
8. ✅ Enable feedback widget
9. ✅ Set up analytics tracking
10. ✅ Create monthly maintenance calendar

---

## Resources

- **BetterDocs Documentation**: https://betterdocs.co/docs/
- **Markdown Guide**: https://www.markdownguide.org/
- **Technical Writing Best Practices**: https://developers.google.com/tech-writing
- **Code Syntax Highlighting**: Use triple backticks with language identifier (```python, ```bash, etc.)

---

## Notes

- Prioritize completeness over perfection - ship docs early and iterate
- Encourage community contributions via GitHub
- Keep docs in sync with firmware releases
- Use consistent terminology across all docs
- Add version numbers to docs that reference specific firmware versions
- Include "Last Updated" date on each doc
- Consider video tutorials for complex visual tasks (3D assembly, soldering)
