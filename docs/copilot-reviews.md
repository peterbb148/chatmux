# Setting Up Automatic Copilot Reviews

This guide explains how to enable automatic GitHub Copilot code reviews for all pull requests in the Chatmux repository.

## Prerequisites

- GitHub Copilot subscription (Individual, Business, or Enterprise)
- Repository admin access

## Manual Review Process

By default, you can manually request Copilot reviews on any PR:

1. Open a pull request
2. In the right sidebar, find the "Reviewers" section
3. Click on "Reviewers" and select "Copilot" from the dropdown
4. Copilot will analyze your code and provide feedback

## Enabling Automatic Reviews

To have Copilot automatically review every pull request:

### Step 1: Access Repository Settings

1. Navigate to the repository on GitHub
2. Click on "Settings" tab
3. In the left sidebar, find "Code, planning, and automation"
4. Click on "Repository" → "Rulesets"

### Step 2: Create a Branch Ruleset

1. Click "New ruleset" → "New branch ruleset"
2. Give your ruleset a name (e.g., "Automatic Copilot Reviews")
3. Under "Target branches", add patterns for branches you want to protect:
   - `main` or `master` for the default branch
   - `**/*` for all branches
   - Custom patterns as needed

### Step 3: Configure Copilot Review

1. In the ruleset configuration, find the "Pull request" section
2. Check the box for "Request pull request review from Copilot"
3. Configure any additional rules as needed

### Step 4: Activate the Ruleset

1. Under "Enforcement status", select "Active"
2. Click "Create" to save the ruleset

## How Automatic Reviews Work

Once enabled:
- Copilot will automatically review all new pull requests matching your ruleset
- Reviews appear as comments on specific lines of code
- Copilot may suggest fixes that can be applied with one click
- You can still request additional reviews by clicking the refresh icon next to Copilot's name

## Important Notes

- Copilot doesn't automatically re-review when you push new changes
- To request a re-review, click the button next to Copilot's name in the Reviewers menu
- Copilot review comments can be resolved, hidden, or reacted to like human reviews
- Comments you add to Copilot's reviews are visible to humans but not to Copilot

## Workflow Integration

This repository includes a GitHub Action that adds a helpful comment to new PRs explaining how to request reviews from both Copilot and Claude Code. See `.github/workflows/copilot-review.yml` for details.

## Troubleshooting

If Copilot reviews aren't available:
1. Verify your GitHub Copilot subscription is active
2. Check that Copilot is enabled for your organization
3. Ensure the repository allows Copilot access
4. Confirm the ruleset is active and properly configured

For more information, see the [official GitHub documentation](https://docs.github.com/en/copilot/using-github-copilot/code-review/configuring-automatic-code-review-by-copilot).
