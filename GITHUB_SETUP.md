# GitHub Repository Setup for HACS

This guide walks you through setting up the MSpa integration as a HACS-compatible GitHub repository.

## 📋 **Prerequisites**

- GitHub account
- Git installed on your machine
- Files from the MSpa integration development

## 🚀 **Step 1: Create GitHub Repository**

1. **Create Repository**:
   - Go to GitHub and create a new repository
   - Name: `spa` (as created: https://github.com/Team5ooo/spa)
   - Description: "MSpa Home Assistant Integration - Control your MSpa devices"
   - Make it **Public** (required for HACS)
   - Initialize with README: **No** (we have our own)

2. **Clone Repository**:
   ```bash
   git clone https://github.com/Team5ooo/spa.git
   cd spa
   ```

## 📁 **Step 2: Repository Structure**

Your repository should have this structure:
```
spa/
├── README.md
├── LICENSE
├── hacs.json
├── info.md
├── GITHUB_SETUP.md
├── custom_components/
│   └── mspa/
│       ├── __init__.py
│       ├── manifest.json
│       ├── const.py
│       ├── config_flow.py
│       ├── mspaapi.py
│       ├── sensor.py
│       ├── switch.py
│       ├── binary_sensor.py
│       ├── strings.json
│       ├── CLAUDE.md
│       └── translations/
│           └── en.json
```

## 📦 **Step 3: Copy Files**

Copy all the integration files to the repository:

```bash
# Create directory structure
mkdir -p custom_components/mspa/translations

# Copy main files
cp /path/to/mspa/*.py custom_components/mspa/
cp /path/to/mspa/*.json custom_components/mspa/
cp /path/to/mspa/CLAUDE.md custom_components/mspa/
cp /path/to/mspa/translations/en.json custom_components/mspa/translations/

# Copy repository files
cp /path/to/mspa/README.md ./
cp /path/to/mspa/LICENSE ./
cp /path/to/mspa/hacs.json ./
cp /path/to/mspa/info.md ./
cp /path/to/mspa/.gitignore ./
```

## 🔧 **Step 4: Update URLs**

Update the following files to use your actual GitHub username:

**1. README.md**:
- Replace `yourusername` with your GitHub username
- Update all repository URLs

**2. manifest.json**:
- Update `documentation` and `issue_tracker` URLs
- Replace `yourusername` with your GitHub username

**3. hacs.json**:
- Update any URLs if needed

## 📝 **Step 5: Initial Commit**

```bash
git add .
git commit -m "Initial commit: MSpa Home Assistant Integration

- Complete integration with working authentication
- Support for sensors, switches, and binary sensors
- HACS compatible with proper metadata
- Comprehensive documentation and setup guide

🎉 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

## 🏷️ **Step 6: Create First Release**

1. **Tag the Release**:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0: Initial stable release"
   git push origin v1.0.0
   ```

2. **Create GitHub Release**:
   - Go to your GitHub repository
   - Click "Releases" → "Create a new release"
   - Tag: `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Description:
     ```markdown
     # MSpa Home Assistant Integration v1.0.0

     ## 🎉 Initial Release

     This is the first stable release of the MSpa Home Assistant Integration.

     ### Features
     - ✅ Complete authentication system with automatic token management
     - ✅ Temperature monitoring (water temperature and target temperature)
     - ✅ Device control (heater, filter, bubbles, ozone, UVC, safety lock)
     - ✅ Status monitoring with binary sensors
     - ✅ HACS compatible for easy installation
     - ✅ Comprehensive documentation and setup guide

     ### Installation
     - Install via HACS (recommended)
     - Manual installation supported

     ### Requirements
     - Home Assistant 2023.1.0 or higher
     - MSpa account credentials
     - Device ID and Product ID from MSpa app

     ### Authentication
     Uses your MSpa account username/password - no manual token required!

     ## 🔧 Technical Details
     - Discovered authentication endpoint through MITM analysis
     - Extracted app secret from Android APK reverse engineering
     - Implemented proper signature generation algorithm
     - Full compliance with MSpa API security requirements

     ## 📖 Documentation
     See the [README](README.md) for installation and setup instructions.
     ```

3. **Attach Files** (optional):
   - You can attach a zip file of the integration
   - This is helpful for manual installation

## 🏪 **Step 7: HACS Installation**

### For Users (Installation Instructions):

1. **Add Custom Repository**:
   - Open HACS in Home Assistant
   - Go to "Integrations"
   - Click the 3-dot menu → "Custom repositories"
   - Add URL: `https://github.com/Team5ooo/spa`
   - Category: "Integration"
   - Click "Add"

2. **Install Integration**:
   - Find "MSpa" in the HACS integrations list
   - Click "Download"
   - Restart Home Assistant

3. **Configure Integration**:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "MSpa"
   - Enter your MSpa credentials

### For HACS Default Repository (Optional):

To get your integration added to the default HACS repository:

1. **Meet Requirements**:
   - Repository must be public
   - Must have proper documentation
   - Must follow Home Assistant conventions
   - Must have releases with proper versioning

2. **Submit to HACS**:
   - Go to [HACS repository](https://github.com/hacs/default)
   - Follow their submission process
   - This takes time for review and approval

## 🚀 **Step 8: Maintenance**

### Future Updates:
```bash
# Make changes to your code
git add .
git commit -m "Description of changes"
git push origin main

# Create new release
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# Create GitHub release as before
```

### Version Numbers:
- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features
- **Patch** (1.0.0 → 1.0.1): Bug fixes

## ✅ **Verification Checklist**

Before releasing, verify:
- [ ] All files are in correct locations
- [ ] URLs are updated with your username
- [ ] `hacs.json` is properly formatted
- [ ] `manifest.json` has correct version and URLs
- [ ] README.md has complete installation instructions
- [ ] Code is tested and working
- [ ] Repository is public
- [ ] First release is tagged and published

## 🎉 **Success!**

Once complete, users can install your MSpa integration via HACS!