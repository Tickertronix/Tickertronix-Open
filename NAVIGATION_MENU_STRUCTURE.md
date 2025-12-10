# Recommended Navigation Menu Structure for Tickertronix.com

## Overview
This document outlines the recommended navigation menu structure to reflect the site's transformation from a "live market ticker app" to an **open-source DIY maker hub** with a clear hub-client architecture.

## Implementation
Navigate to **WordPress Admin Panel → Appearance → Menus** to implement this structure.

---

## Primary Navigation Menu

### 1. Home
- **Page ID:** 14
- **URL:** `/home/`
- **Purpose:** Landing page emphasizing DIY builder focus with hub-client architecture

### 2. Get Started (Dropdown)
Create a new custom menu item or category for the DIY/maker workflow:

#### 2.1 🍓 Raspberry Pi Hub (Start Here)
- **Page ID:** 274
- **URL:** `/raspberry-pi-price-hub/`
- **Purpose:** **Required first step** - central server setup guide
- **Badge:** Consider adding "REQUIRED" or "START HERE" label in menu

#### 2.2 📊 Hardware Comparison
- **Page ID:** 275
- **URL:** `/hardware-comparison/`
- **Purpose:** Help users choose the right hardware combination
- **Description:** Compare all platforms and see recommended setup tiers

#### 2.3 📺 CYD Ticker Build
- **Page ID:** 211
- **URL:** `/tickertronix-diy-hub/the-20-dollar-ticker-cyd-ticker/`
- **Purpose:** ESP32 touchscreen display build guide (client device)

#### 2.4 🔲 Matrix Portal Build
- **Find and link the Matrix Portal build guide page**
- **Purpose:** LED scrolling display build guide (client device)

### 3. Documentation
- **Page ID:** 19
- **URL:** `/docs/` (BetterDocs powered)
- **Purpose:** Comprehensive technical documentation hub
- **Subcategories to organize:**
  - API Reference
  - Configuration Guides
  - Troubleshooting
  - Firmware Updates

### 4. Community
- **Page ID:** 34
- **URL:** `/community/` or `/forum/`
- **Purpose:** User forums, discussions, project showcase
- **Consider adding:**
  - Gallery of user builds
  - Featured projects
  - Discord/Slack link

### 5. Store
- **Page ID:** 17
- **URL:** `/store/`
- **Purpose:** DIY kits, components, 3D files
- **Future additions:**
  - Pre-assembled kits
  - Premium support subscriptions
  - 3D STL file bundles

### 6. GitHub (External Link)
- **URL:** https://github.com/yourusername/tickertronix-price-hub
- **Purpose:** Direct link to open-source repository
- **Icon:** GitHub logo
- **Opens in:** New tab

---

## Secondary Navigation (Footer)

### Column 1: Quick Start
- Raspberry Pi Hub Setup
- Hardware Requirements
- Getting Started Guide

### Column 2: Resources
- Documentation
- API Reference
- Troubleshooting
- FAQ

### Column 3: Community
- Forum
- Discord
- Project Gallery
- Contribute

### Column 4: Legal
- Privacy Policy
- Terms of Service
- License (Open Source)

---

## Mobile Navigation Considerations

### Hamburger Menu Order (Mobile):
1. Home
2. **START HERE** (bold/highlighted)
   - Raspberry Pi Hub
3. Get Started
   - Hardware Comparison
   - CYD Ticker Build
   - Matrix Portal Build
4. Documentation
5. Community
6. Store
7. GitHub

---

## Menu Item Styling Recommendations

### CSS Classes to Add:

```css
/* Highlight the required starting point */
.menu-item-274 {
  /* Raspberry Pi Hub */
  background: #4A3AFD;
  border-radius: 4px;
  padding: 4px 8px;
}

.menu-item-274 a {
  color: #ffffff !important;
  font-weight: 600;
}

/* Add badge to "Start Here" */
.menu-item-274::after {
  content: "REQUIRED";
  background: #FF6B6B;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  margin-left: 8px;
  vertical-align: middle;
}
```

---

## Implementation Steps

1. **Backup Current Menu**: Export existing menu structure before changes
2. **Create New Menu** (if needed): Name it "DIY Main Navigation"
3. **Add Pages**:
   - Drag pages from the left sidebar into the menu structure
   - Use the "Custom Links" option for GitHub
4. **Organize Hierarchy**:
   - Indent child items under parent dropdown menus
   - Ensure "Raspberry Pi Hub" is prominently placed
5. **Add CSS Classes**:
   - Enable "CSS Classes" in Screen Options (top right)
   - Add custom classes to menu items for styling
6. **Assign Menu Location**: Set to "Primary Menu" or your theme's main navigation location
7. **Save & Test**: Save menu and test on desktop and mobile

---

## BetterDocs Integration

The Documentation section (Page ID 19) should be configured with BetterDocs to organize technical docs into categories:

### Suggested Doc Categories:
- **Getting Started** (Installation, quick start, first build)
- **Hardware Guides** (Pi Hub, CYD, Matrix Portal)
- **API Reference** (Endpoints, authentication, data formats)
- **Configuration** (WiFi setup, ticker selection, display settings)
- **Troubleshooting** (Common issues, error codes, logs)
- **Advanced** (Custom firmware, API integration, multi-hub setups)

Configure these in: **WordPress Admin → BetterDocs → Settings → Doc Categories**

---

## 3D Viewer Plugin Setup

Once enabled, add 3D viewer shortcodes to relevant build guide pages:

```
[3dviewer id="123"]  <!-- CYD case STL preview -->
[3dviewer id="124"]  <!-- Matrix Portal mount STL preview -->
```

Upload STL files to: **Media Library → Add New → Upload 3D Files**

---

## Key Messaging in Menu

All menu items should support the core messaging:
- ✅ Open source (no subscriptions)
- ✅ DIY-friendly (step-by-step guides)
- ✅ Hub-client architecture (central Pi Hub + display clients)
- ✅ Free market data (Alpaca API)
- ✅ Local-first (runs on your network)

---

## Page IDs Reference

| Page | ID | URL |
|------|-----|-----|
| Home | 14 | `/home/` |
| Raspberry Pi Hub | 274 | `/raspberry-pi-price-hub/` |
| Hardware Comparison | 275 | `/hardware-comparison/` |
| CYD Ticker Build | 211 | `/tickertronix-diy-hub/the-20-dollar-ticker-cyd-ticker/` |
| Docs | 19 | `/docs/` |
| Community/Forum | 34 | `/community/` or `/forum/` |
| Store | 17 | `/store/` |

---

## Next Steps

1. Implement this menu structure in WordPress admin panel
2. Enable 3D Viewer plugin for STL file previews on build pages
3. Configure BetterDocs categories for documentation organization
4. Add GitHub repository link to primary navigation
5. Test navigation flow on desktop and mobile
6. Add menu item badges/highlights for "Start Here" items

---

## Notes

- The Raspberry Pi Hub should always be the most prominent entry point
- Consider adding a persistent "Get Started" banner/button on all pages
- Mobile navigation should prioritize the hub-client workflow
- Store section can be minimal initially, expanded as kits become available
