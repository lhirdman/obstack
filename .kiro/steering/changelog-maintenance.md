# Changelog Maintenance Rules

## Mandatory Changelog Updates

**CRITICAL RULE**: Whenever you make significant changes to the codebase, configuration, or project structure, you MUST update the CHANGELOG.md file to document these changes.

## When to Update CHANGELOG.md

You MUST update the changelog in these scenarios:

1. **Code Implementation**: When completing tasks from specs or implementing new features
2. **Configuration Changes**: Updates to package.json, requirements.txt, Docker configs, etc.
3. **Architecture Changes**: Modifications to project structure, new components, or design changes
4. **Bug Fixes**: Any fixes to existing functionality
5. **Breaking Changes**: Changes that affect existing APIs or behavior
6. **Dependency Updates**: Major version updates or new dependencies added
7. **Documentation Updates**: Significant additions to docs, READMEs, or guides

## Changelog Format

Use [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to ObservaStack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes

## [1.0.0] - YYYY-MM-DD
### Added
- Initial release
```

## Implementation Process

1. **Check Current Time**: Use `mcp_time_get_current_time` for accurate dates
2. **Identify Change Type**: Added, Changed, Deprecated, Removed, Fixed, Security
3. **Write Clear Description**: What was changed and why
4. **Use Present Tense**: "Add user authentication" not "Added user authentication"
5. **Reference Issues/PRs**: Link to relevant tickets when applicable

## Entry Guidelines

### Good Changelog Entries:
- `Add multi-tenant authentication system with JWT support`
- `Update React to version 19.1.0 for improved performance`
- `Fix search results not displaying for non-admin users`
- `Remove deprecated PropTypes in favor of TypeScript interfaces`

### Bad Changelog Entries:
- `Updated stuff`
- `Bug fixes`
- `Various improvements`
- `Code cleanup`

## Changelog Location

- **Main Project**: `CHANGELOG.md` in project root
- **Frontend**: `observastack-app/frontend/CHANGELOG.md` (if needed)
- **Backend**: `observastack-app/bff/CHANGELOG.md` (if needed)

## Automation Integration

- Update changelog BEFORE committing code changes
- Include changelog updates in the same commit as the feature/fix
- Use conventional commit messages that align with changelog entries

## Version Management

- Keep `[Unreleased]` section at top for ongoing work
- Create dated version sections when releasing
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Link version tags to GitHub releases when applicable

## Example Workflow

```
1. Complete a task (e.g., implement authentication)
2. Check current time with mcp_time_get_current_time
3. Update CHANGELOG.md under [Unreleased] > Added
4. Commit both code changes and changelog update together
```

## Enforcement

This rule applies to ALL significant changes and MUST be followed consistently. A well-maintained changelog is essential for:

- **Project History**: Understanding what changed and when
- **Release Notes**: Generating release documentation
- **Debugging**: Tracking when issues were introduced or fixed
- **Team Communication**: Keeping everyone informed of changes
- **User Documentation**: Helping users understand updates

Failure to maintain the changelog is considered a critical oversight that reduces project maintainability.