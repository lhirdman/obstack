# ObservaStack Version Updates - August 2025

## Summary of Changes

This document outlines the version updates made to bring ObservaStack up to the latest stable versions of all major dependencies as of August 2025.

## Node.js Version Strategy

- **Current LTS**: Node.js 22.12+ (recommended for production)
- **Node.js 24**: Available but not LTS until October 2025
- **Decision**: Using Node.js 22.12+ for stability while being ready for 24 LTS transition

## Frontend Stack Updates

### Major Version Updates
- **Vite**: 6.0.3 → 7.0.0 (major update)
  - New default browser target: 'baseline-widely-available'
  - Improved build performance with Rolldown integration
  - Node.js 20.19+ or 22.12+ required

- **React Router**: 7.1.0 → 7.6.2 (patch update)
  - Latest stable with data APIs
  - Improved type safety and performance

- **TypeScript**: 5.7.2 → 5.9.2 (minor update)
  - Latest stable release with bug fixes

- **TanStack Query**: 5.62.0 → 5.84.1 (minor update)
  - Performance improvements and bug fixes
  - Better React 19 compatibility

### Node.js Engine Requirements
- **Updated**: `>=20.18.0` → `>=22.12.0`
- **Added**: `.nvmrc` file specifying Node.js 22.12.0

## Backend Stack (No Changes Needed)

- **FastAPI**: 0.115.6 (already latest)
- **Python**: 3.12+ (already current recommendation)
- **uvicorn**: 0.32.1 (already latest)
- **Pydantic**: 2.10.3 (already latest)

## Breaking Changes & Migration Notes

### Vite 7.0 Changes
- Default browser target changed from 'modules' to 'baseline-widely-available'
- Improved Rolldown integration for better performance
- Some deprecated APIs removed (none affecting our current config)

### React Router 7.6.2
- No breaking changes from 7.1.0, mostly bug fixes and improvements

### TypeScript 5.9.2
- No breaking changes, improved type inference and performance

## Next Steps

1. **Install updated dependencies**:
   ```bash
   cd observastack-app/frontend
   npm install
   ```

2. **Verify Node.js version**:
   ```bash
   nvm use  # Uses .nvmrc file
   node --version  # Should show v22.12.0 or higher
   ```

3. **Test the application**:
   ```bash
   npm run dev
   npm run build
   npm run test
   ```

4. **Update CI/CD pipelines** to use Node.js 22.12+

## Future Considerations

- **Node.js 24 LTS**: Plan to upgrade in October 2025 when it becomes LTS
- **Vite 8**: Monitor for release and new features
- **React 20**: Keep an eye on React's roadmap for next major version

## Compatibility Matrix

| Component | Version | Node.js Requirement | Status |
|-----------|---------|---------------------|---------|
| Vite | 7.0.0 | 20.19+ or 22.12+ | ✅ Updated |
| React | 19.1.0 | 18+ | ✅ Current |
| TypeScript | 5.9.2 | 14+ | ✅ Updated |
| React Router | 7.6.2 | 18+ | ✅ Updated |
| TanStack Query | 5.84.1 | 18+ | ✅ Updated |
| FastAPI | 0.115.6 | Python 3.8+ | ✅ Current |

All versions are now aligned with the latest stable releases as of August 2025.