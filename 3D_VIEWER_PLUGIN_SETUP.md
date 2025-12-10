# 3D Viewer Plugin Configuration Guide

## Overview
The 3D Viewer plugin (version 1.8.0) is currently installed but **inactive** on tickertronix.com. This guide provides step-by-step instructions for enabling and configuring the plugin to display 3D printable STL files for DIY hardware builds.

## Purpose
Enable users to preview 3D printable case files, mounts, and enclosures directly on build guide pages without downloading files first.

---

## Step 1: Activate the Plugin

1. Navigate to **WordPress Admin Panel → Plugins → Installed Plugins**
2. Locate **"3D Viewer"** (version 1.8.0) in the plugin list
3. Click **"Activate"** button
4. Verify activation by checking for "3D Viewer" in the WordPress admin sidebar

---

## Step 2: Upload 3D Model Files

### Recommended 3D Files to Upload:

#### CYD Ticker Models:
- `cyd_case_bottom.stl` - Bottom half of enclosure
- `cyd_case_top.stl` - Top half with screen cutout
- `cyd_desk_stand.stl` - Optional desktop stand

#### Matrix Portal Models:
- `matrix_mount_wall.stl` - Wall mounting bracket
- `matrix_mount_desk.stl` - Desktop stand
- `matrix_dual_spacer.stl` - Spacer for dual-panel setups

#### Raspberry Pi Hub Models:
- `pi_zero_case.stl` - Compact case for Pi Zero 2 W
- `pi_4_case.stl` - Full case for Pi 4
- `pi_vesa_mount.stl` - VESA mount adapter for monitor attachment

### Upload Process:

1. Navigate to **Media Library → Add New**
2. **Upload STL files** from the project repository:
   - Look for `.stl` files in `/3d_models/` or similar directory
   - Drag and drop or click "Select Files"
3. After upload, **note the Media ID** for each file (shown in URL: `post=123`)
4. Add descriptive **Alt Text** and **Description** for each model:
   - Example: "CYD Ticker - Bottom Case Half (Print Time: ~3 hours)"

---

## Step 3: Configure Plugin Settings

Navigate to **WordPress Admin → 3D Viewer → Settings**

### General Settings:

```
Default Viewer Type: WebGL Viewer
Default Width: 100%
Default Height: 400px
Enable Fullscreen: ✅ Yes
Enable Auto-Rotate: ✅ Yes (slow speed)
Enable Grid: ✅ Yes
Enable Wireframe Toggle: ✅ Yes
Background Color: #00031c (match site dark theme)
Model Color: #4A3AFD (match site purple accent)
```

### Advanced Settings:

```
Camera Position: Default (isometric)
Lighting: Standard (ambient + directional)
Zoom Controls: ✅ Enable mouse wheel zoom
Pan Controls: ✅ Enable click-and-drag pan
Mobile Touch: ✅ Enable touch gestures
Loading Animation: ✅ Show spinner
```

### Performance Settings:

```
Max Polygon Count: 100,000 (optimize for mobile)
Texture Quality: Medium (balance quality vs load time)
Enable Caching: ✅ Yes
Lazy Loading: ✅ Yes (load when scrolled into view)
```

---

## Step 4: Add 3D Viewers to Build Pages

### Using Shortcodes:

Once files are uploaded and plugin is configured, add viewers to pages using shortcodes:

#### Basic Shortcode:
```
[3dviewer id="123"]
```
Replace `123` with the Media ID from Step 2.

#### Advanced Shortcode with Options:
```
[3dviewer id="123" width="100%" height="500px" autorotate="true" wireframe="false" background="#00031c"]
```

### Where to Add Viewers:

#### CYD Ticker Build Page (ID 211):

Add to the "3D Printable Case" section:

```html
<h3>🖨️ 3D Printable Enclosure</h3>
<p>Print your own case in two parts (bottom and top). Supports any FDM printer with 150mm+ bed.</p>

<h4>Bottom Case Half</h4>
[3dviewer id="XXX" height="400px" autorotate="true"]
<ul>
  <li><strong>Print Time:</strong> ~3 hours</li>
  <li><strong>Material:</strong> PLA or PETG</li>
  <li><strong>Supports:</strong> None required</li>
</ul>

<h4>Top Case Half</h4>
[3dviewer id="XXX" height="400px" autorotate="true"]
<ul>
  <li><strong>Print Time:</strong> ~2.5 hours</li>
  <li><strong>Material:</strong> PLA or PETG</li>
  <li><strong>Supports:</strong> None required</li>
</ul>

<p><a href="/download/cyd-case-stl-bundle.zip" class="button">📥 Download All STL Files</a></p>
```

#### Matrix Portal Build Page:

Add to the "Mounting Options" section:

```html
<h3>🔧 Mounting Options</h3>

<h4>Wall Mount Bracket</h4>
[3dviewer id="XXX" height="400px" autorotate="true"]
<p>Secure your Matrix Portal to any wall with keyhole mounting slots.</p>

<h4>Desktop Stand</h4>
[3dviewer id="XXX" height="400px" autorotate="true"]
<p>Angled stand for optimal desk viewing. Includes cable management channel.</p>

<p><a href="/download/matrix-mounts-stl-bundle.zip" class="button">📥 Download All STL Files</a></p>
```

#### Raspberry Pi Hub Page (ID 274):

Add to a new "Optional Enclosures" section:

```html
<h2>🏠 Optional Enclosures</h2>
<p>While the Pi Hub runs headless and doesn't require an enclosure, you can 3D print protective cases for cleaner installations.</p>

<h3>Pi Zero 2 W Case</h3>
[3dviewer id="XXX" height="400px" autorotate="true"]
<p>Compact case with ventilation slots and SD card access. Wall mountable.</p>

<h3>Pi 4 Case with Fan Mount</h3>
[3dviewer id="XXX" height="400px" autorotate="true"]
<p>Full enclosure with 30mm fan mount for active cooling. Includes GPIO access.</p>

<p><a href="/download/pi-cases-stl-bundle.zip" class="button">📥 Download All STL Files</a></p>
```

---

## Step 5: Create a 3D Files Download Page

Consider creating a dedicated page for all 3D printable files:

**Page Title:** "3D Printable Files"
**URL:** `/3d-files/` or `/downloads/stl-files/`

### Content Structure:

```html
<h1>3D Printable Files</h1>
<p>All our 3D printable cases, mounts, and accessories are open-source and free to download. Print at home or use a 3D printing service.</p>

<h2>🖨️ Printing Guidelines</h2>
<ul>
  <li><strong>Material:</strong> PLA recommended for indoor use, PETG for durability</li>
  <li><strong>Layer Height:</strong> 0.2mm standard, 0.15mm for finer details</li>
  <li><strong>Infill:</strong> 20% for cases, 30% for structural mounts</li>
  <li><strong>Supports:</strong> Most models print support-free</li>
</ul>

<h2>📦 CYD Ticker Files</h2>
<div class="file-grid">
  <div class="file-card">
    [3dviewer id="XXX" height="300px"]
    <h3>CYD Case Bottom</h3>
    <p>Print time: ~3 hours | No supports</p>
    <a href="/download/cyd_case_bottom.stl">Download STL</a>
  </div>

  <div class="file-card">
    [3dviewer id="XXX" height="300px"]
    <h3>CYD Case Top</h3>
    <p>Print time: ~2.5 hours | No supports</p>
    <a href="/download/cyd_case_top.stl">Download STL</a>
  </div>
</div>

<h2>🔲 Matrix Portal Files</h2>
<!-- Similar structure for Matrix Portal files -->

<h2>🍓 Raspberry Pi Hub Files</h2>
<!-- Similar structure for Pi Hub files -->

<h2>📋 License</h2>
<p>All 3D models are released under <strong>Creative Commons Attribution 4.0</strong> (CC BY 4.0). You are free to:</p>
<ul>
  <li>Print for personal use</li>
  <li>Modify and remix designs</li>
  <li>Sell printed parts (attribution required)</li>
  <li>Share and redistribute</li>
</ul>
```

---

## Step 6: Test and Optimize

### Testing Checklist:

- [ ] Test 3D viewer on desktop Chrome, Firefox, Safari
- [ ] Test on mobile devices (iOS Safari, Android Chrome)
- [ ] Verify auto-rotate works smoothly
- [ ] Check fullscreen mode functionality
- [ ] Test zoom and pan controls
- [ ] Verify lazy loading on pages with multiple models
- [ ] Check load times (optimize if > 3 seconds)

### Optimization Tips:

1. **Reduce Polygon Count**: Use mesh simplification tools if models are >50k polygons
2. **Compress STL Files**: Use online STL compression tools
3. **Add Loading Placeholder**: Show thumbnail image while 3D model loads
4. **Implement CDN**: Serve STL files from a CDN for faster loading
5. **Add Download Links**: Always provide direct STL download as alternative to viewer

---

## Step 7: SEO and Accessibility

### Image Alt Text for Thumbnails:
```
"3D preview of CYD Ticker bottom case - STL file for 3D printing"
```

### Add Schema Markup:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "3DModel",
  "name": "CYD Ticker Case Bottom",
  "description": "3D printable bottom half of CYD ticker enclosure",
  "encodingFormat": "model/stl",
  "license": "https://creativecommons.org/licenses/by/4.0/"
}
</script>
```

---

## Troubleshooting

### Issue: 3D Viewer Not Loading

**Causes:**
- JavaScript errors in browser console
- STL file too large (>10MB)
- Browser WebGL disabled

**Solutions:**
1. Check browser console for errors (F12)
2. Enable WebGL in browser settings
3. Reduce STL file size using mesh simplification
4. Try different browser (Chrome recommended)

### Issue: Viewer Lags on Mobile

**Causes:**
- High polygon count
- Multiple viewers on same page
- Mobile GPU limitations

**Solutions:**
1. Create mobile-optimized STL files (<20k polygons)
2. Use lazy loading
3. Reduce number of viewers per page
4. Add "Tap to load" option for mobile

### Issue: Models Display Incorrect Colors

**Causes:**
- Plugin settings conflict
- Theme CSS override

**Solutions:**
1. Check plugin background/model color settings
2. Add custom CSS to override theme styles:
```css
.viewer-3d-canvas {
  background-color: #00031c !important;
}
```

---

## Integration with Store (Future)

When selling DIY kits in the store, integrate 3D viewers into product pages:

1. Add 3D viewer to WooCommerce product gallery
2. Show printable parts in "What's Included" section
3. Offer premium "Pre-Printed Kit" option alongside STL downloads
4. Bundle STL files as downloadable product (free or paid)

Example WooCommerce shortcode:
```
[product_page id="456"]
[3dviewer id="123" height="400px"]
```

---

## Maintenance

### Regular Updates:

- **Weekly**: Check for plugin updates in WordPress admin
- **Monthly**: Review viewer analytics to identify popular models
- **Quarterly**: Optimize STL files based on user feedback
- **Annually**: Audit and remove outdated model versions

### Analytics to Track:

- 3D viewer load times
- Interaction rate (how many users rotate/zoom models)
- Download conversions (viewer → download)
- Mobile vs desktop usage
- Error rates

---

## Next Steps

1. ✅ Activate 3D Viewer plugin via WordPress admin
2. ✅ Upload initial STL files for all three platforms
3. ✅ Configure plugin settings (colors, performance)
4. ✅ Add viewers to CYD, Matrix Portal, and Pi Hub pages
5. ✅ Create dedicated 3D Files download page
6. ✅ Test on desktop and mobile devices
7. ✅ Add schema markup for SEO
8. ✅ Document printing guidelines for users

---

## Resources

- **Plugin Documentation**: Check WordPress admin → 3D Viewer → Help
- **STL File Optimization**: Use MeshLab or Blender for polygon reduction
- **WebGL Browser Support**: https://caniuse.com/webgl
- **CC BY 4.0 License**: https://creativecommons.org/licenses/by/4.0/

---

## Notes

- Consider creating a "Submit Your Design" page for community contributions
- Add print-time estimates and material requirements to all models
- Create beginner-friendly "First 3D Print" tutorial linked from 3D viewer pages
- Showcase user prints in a gallery (Instagram integration?)
