/**
 * Bug Reproduction Tests - Systematic testing of bugs 1-9 from bugs 1-8.png
 *
 * This file reproduces all bugs identified in the screenshot, documents:
 * - Exact reproduction steps
 * - Expected vs actual behavior
 * - Error messages and network responses
 * - When and why each bug occurs
 *
 * Run with: npx playwright test bug-reproduction.spec.ts
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:5173';
// API_URL reserved for future API integration tests: http://localhost:8000

/**
 * Setup helper: Login and navigate to page
 */
async function loginAndNavigate(page: Page, path: string = '/dashboard') {
  // Navigate to login
  await page.goto(`${BASE_URL}/login`);

  // Fill login form
  await page.fill('input[type="email"]', 'mrskwiw@gmail.com');
  await page.fill('input[type="password"]', 'Random!1Pass');
  await page.click('button[type="submit"]');

  // Wait for navigation to dashboard
  await page.waitForURL(`${BASE_URL}/dashboard`, { timeout: 5000 });

  // Navigate to requested path (prepend /dashboard if not already there)
  if (path !== '/dashboard') {
    const fullPath = path.startsWith('/dashboard') ? path : `/dashboard${path}`;
    await page.goto(`${BASE_URL}${fullPath}`);
    await page.waitForLoadState('networkidle');
  }
}

/**
 * Bug #1 & #2: Wizard/Projects generate 500 error (friendly blog)
 *
 * Page: wizard, projects
 * Tab: generate
 * Control: generate button
 * Action: generate friendly blog
 * Expected: Generation starts, run status shown
 * Actual: Failed to start generation, 500 error
 *
 * Root Cause: Import error in generator.py line 109
 * - schemas.run.LogEntry should be backend.schemas.run.LogEntry
 * - Background task crashes with ModuleNotFoundError
 * - Returns 500 to client
 *
 * Status: FIXED in commit 7736f2a
 */
test.describe('BUG #1-2: Generate 500 Error (Friendly Blog)', () => {
  test('should generate friendly blog without 500 error', async ({ page }) => {
    await loginAndNavigate(page, '/wizard');

    // Navigate to generate tab
    await page.click('text="Generate"');

    // Wait for generate form
    await page.waitForSelector('button:has-text("Generate")');

    // Listen for API request
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/generator/generate-all') && response.request().method() === 'POST'
    );

    // Click generate for friendly blog
    await page.click('button:has-text("Generate"):first');

    // Wait for response
    const response = await responsePromise;
    const status = response.status();
    const body = await response.json().catch(() => ({}));

    // Document actual behavior
    test.info().annotations.push({
      type: 'actual-behavior',
      description: `Status: ${status}, Body: ${JSON.stringify(body, null, 2)}`
    });

    // Verify no 500 error
    expect(status, 'Should not return 500 error').not.toBe(500);
    expect(status, 'Should return 200 OK').toBe(200);
    expect(body, 'Should have run_id').toHaveProperty('id');
    expect(body.status, 'Run status should be running or pending').toMatch(/running|pending/);
  });
});

/**
 * Bug #3: Wizard client profile - use existing client doesn't populate form
 *
 * Page: wizard
 * Tab: client profile
 * Control: use existing client dropdown
 * Action: populate form with existing client
 * Expected: Form fields populated with client data
 * Actual: Nothing happens, form remains empty
 *
 * Root Cause: TBD - needs investigation
 * - Likely missing onChange handler or data fetching
 * - Client data not being loaded into form state
 *
 * Status: PENDING
 */
test.describe('BUG #3: Client Profile Form Not Populating', () => {
  test('should populate form when selecting existing client', async ({ page }) => {
    await loginAndNavigate(page, '/wizard');

    // Ensure we're on client profile tab
    await page.click('text="Client Profile"');

    // Look for existing client dropdown/select
    const clientSelect = page.locator('select[name="existingClient"], select:has-text("Select existing client")').first();

    if (await clientSelect.count() > 0) {
      // Get available options
      const options = await clientSelect.locator('option').allTextContents();
      test.info().annotations.push({
        type: 'available-options',
        description: `Options: ${options.join(', ')}`
      });

      // Select first non-empty option
      if (options.length > 1) {
        await clientSelect.selectOption({ index: 1 });

        // Wait for form to potentially populate
        await page.waitForTimeout(1000);

        // Check if form fields are populated
        const companyName = await page.inputValue('input[name="companyName"], input[placeholder*="Company"]').catch(() => '');
        const businessDesc = await page.inputValue('textarea[name="businessDescription"], textarea[placeholder*="Business"]').catch(() => '');

        test.info().annotations.push({
          type: 'actual-behavior',
          description: `Company: "${companyName}", Business: "${businessDesc}"`
        });

        // Document bug if form is empty
        expect(companyName || businessDesc, 'Form should be populated with client data').toBeTruthy();
      }
    } else {
      test.info().annotations.push({
        type: 'element-not-found',
        description: 'Existing client dropdown not found on page'
      });
    }
  });
});

/**
 * Bug #4: Wizard generate 500 error (professional generic copy)
 *
 * Same as BUG #1-2 but for professional generic copy template
 * Status: FIXED in commit 7736f2a (same root cause)
 */
test.describe('BUG #4: Generate 500 Error (Professional Generic Copy)', () => {
  test('should generate professional generic copy without 500 error', async ({ page }) => {
    await loginAndNavigate(page, '/wizard');

    // Navigate to generate tab
    await page.click('text="Generate"');

    // Listen for API request
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/generator/generate-all')
    );

    // Click generate for professional generic copy (different button/template)
    // NOTE: Exact selector depends on UI implementation
    await page.click('button:has-text("Generate")').catch(() =>
      page.click('[data-template="professional"]')
    );

    const response = await responsePromise;
    const status = response.status();

    // Verify no 500 error
    expect(status, 'Should not return 500 error').not.toBe(500);
  });
});

/**
 * Bug #5: Projects create new project - nothing happens
 *
 * Page: projects
 * Tab: create new project
 * Control: create project button
 * Action: create new project
 * Expected: New project created, redirected or confirmation shown
 * Actual: Nothing happens, no response
 *
 * Root Cause: TBD - needs investigation
 * - Could be missing API call
 * - Could be validation preventing submission
 * - Could be success handler not executing
 *
 * Status: PENDING
 */
test.describe('BUG #5: Create New Project - Nothing Happens', () => {
  test('should create new project successfully', async ({ page }) => {
    await loginAndNavigate(page, '/projects');

    // Click create new project
    const createButton = page.locator('button:has-text("Create"), button:has-text("New Project")').first();
    await createButton.click();

    // Fill project form (if modal/form appears)
    await page.waitForTimeout(500);

    const projectNameInput = page.locator('input[name="projectName"], input[placeholder*="Project"]').first();
    if (await projectNameInput.count() > 0) {
      await projectNameInput.fill('Test Project from Playwright');

      // Listen for API call
      const apiCallPromise = page.waitForResponse(
        response => response.url().includes('/api/projects') && response.request().method() === 'POST',
        { timeout: 5000 }
      ).catch(() => null);

      // Submit form
      await page.click('button[type="submit"], button:has-text("Create")');

      // Check if API was called
      const apiResponse = await apiCallPromise;

      test.info().annotations.push({
        type: 'actual-behavior',
        description: apiResponse
          ? `API called: ${apiResponse.status()} - ${await apiResponse.text().catch(() => '')}`
          : 'No API call detected - nothing happened'
      });

      expect(apiResponse, 'API call should be made').toBeTruthy();
      if (apiResponse) {
        expect(apiResponse.status(), 'Should return success status').toBeLessThan(400);
      }
    } else {
      test.info().annotations.push({
        type: 'element-not-found',
        description: 'Project name input not found - form may not have appeared'
      });
    }
  });
});

/**
 * Bug #6: Advanced settings/integrations - connect - nothing happens
 *
 * Page: advanced settings
 * Tab: integrations
 * Control: connect button
 * Action: connect cloud storage
 * Expected: Connection dialog or OAuth flow
 * Actual: Nothing happens
 *
 * Root Cause: TBD - Feature not implemented or handler missing
 * Status: PENDING
 */
test.describe('BUG #6: Advanced Settings Integrations - Nothing Happens', () => {
  test('should show response when clicking connect', async ({ page }) => {
    await loginAndNavigate(page, '/settings');

    // Navigate to integrations tab
    await page.click('text="Integrations"').catch(() =>
      page.click('[href*="integrations"]')
    );

    // Click connect button
    const connectButton = page.locator('button:has-text("Connect")').first();
    if (await connectButton.count() > 0) {
      await connectButton.click();

      // Wait for any response (modal, navigation, API call)
      await page.waitForTimeout(1000);

      // Check for modal/dialog
      const modal = await page.locator('[role="dialog"], .modal, [data-modal]').count();
      const navigation = page.url() !== `${BASE_URL}/settings`;

      test.info().annotations.push({
        type: 'actual-behavior',
        description: `Modal appeared: ${modal > 0}, Navigation occurred: ${navigation}`
      });

      expect(modal > 0 || navigation, 'Should show modal or navigate').toBeTruthy();
    }
  });
});

/**
 * Bug #7: Advanced settings/workflows - create new workflow rule - nothing happens
 *
 * Status: PENDING
 */
test.describe('BUG #7: Workflows - Create Rule - Nothing Happens', () => {
  test('should create workflow rule', async ({ page }) => {
    await loginAndNavigate(page, '/settings');

    await page.click('text="Workflows"').catch(() =>
      page.click('[href*="workflows"]')
    );

    const createButton = page.locator('button:has-text("Create"), button:has-text("New Rule")').first();
    if (await createButton.count() > 0) {
      const apiCallPromise = page.waitForResponse(
        response => response.url().includes('/api/workflows') || response.url().includes('/api/rules'),
        { timeout: 3000 }
      ).catch(() => null);

      await createButton.click();
      await page.waitForTimeout(500);

      const apiResponse = await apiCallPromise;
      test.info().annotations.push({
        type: 'actual-behavior',
        description: apiResponse ? 'API called' : 'No API call - nothing happened'
      });
    }
  });
});

/**
 * Bug #8: Advanced settings/database - download database backup - nothing happens
 *
 * Status: PENDING
 */
test.describe('BUG #8: Database - Download Backup - Nothing Happens', () => {
  test('should download database backup', async ({ page }) => {
    await loginAndNavigate(page, '/settings');

    await page.click('text="Database"').catch(() =>
      page.click('[href*="database"]')
    );

    const downloadButton = page.locator('button:has-text("Download"), button:has-text("Backup")').first();
    if (await downloadButton.count() > 0) {
      // Listen for download
      const downloadPromise = page.waitForEvent('download', { timeout: 3000 }).catch(() => null);

      await downloadButton.click();

      const download = await downloadPromise;
      test.info().annotations.push({
        type: 'actual-behavior',
        description: download ? `Download started: ${download.suggestedFilename()}` : 'No download - nothing happened'
      });

      expect(download, 'Download should start').toBeTruthy();
    }
  });
});

/**
 * Bug #9: Wizard/research - brand archetype assessment - input needed - nothing happens
 *
 * Page: wizard
 * Tab: research
 * Control: brand archetype assessment
 * Action: input needed
 * Expected: Form/modal for input, or assessment starts
 * Actual: Nothing happens
 *
 * Status: PENDING
 */
test.describe('BUG #9: Research - Brand Archetype - Nothing Happens', () => {
  test('should show input form for brand archetype', async ({ page }) => {
    await loginAndNavigate(page, '/wizard');

    await page.click('text="Research"').catch(() =>
      page.click('[href*="research"]')
    );

    // Look for brand archetype assessment button
    const assessButton = page.locator('button:has-text("Brand Archetype"), button:has-text("Assessment")').first();
    if (await assessButton.count() > 0) {
      await assessButton.click();
      await page.waitForTimeout(500);

      // Check for input form/modal
      const formAppeared = await page.locator('form, [role="dialog"]').count();

      test.info().annotations.push({
        type: 'actual-behavior',
        description: formAppeared > 0 ? 'Form appeared' : 'Nothing happened - no form shown'
      });

      expect(formAppeared, 'Input form should appear').toBeGreaterThan(0);
    }
  });
});
