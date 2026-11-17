const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const indexPath = path.resolve(__dirname, '../../apps/dashboard/static/index.html');
const html = fs.readFileSync(indexPath, 'utf8');

test('nav-research button exists with correct accessibility attributes', () => {
  assert.ok(html.includes('id="nav-research"'), 'nav-research button exists');
  assert.ok(html.includes('aria-controls="tab-research"'), 'aria-controls points to tab-research');
  assert.ok(html.includes("onclick=\"showTab('research')\""), 'onclick calls showTab with research');
});

test('tab-research container exists with tabpanel role and aria-labelledby', () => {
  assert.ok(html.includes('id="tab-research"'), 'tab-research container exists');
  assert.ok(html.includes('role="tabpanel"'), 'role="tabpanel" defined');
  assert.ok(html.includes('aria-labelledby="nav-research"'), 'aria-labelledby points to nav-research');
});

test('all 11 functional UI sections are present in tab-research', () => {
  // 1. Home section & stats
  assert.ok(html.includes('id="res-sec-home"'), 'Home sub-section container');
  assert.ok(html.includes('id="res-stat-tasks"'), 'Tasks count stat');
  assert.ok(html.includes('id="res-stat-reports"'), 'Reports count stat');
  assert.ok(html.includes('id="res-stat-sources"'), 'Sources count stat');
  assert.ok(html.includes('id="res-stat-evidence"'), 'Evidence count stat');
  assert.ok(html.includes('id="res-active-card"'), 'Active research task card');
  assert.ok(html.includes('id="res-active-progbar"'), 'Active progress bar');

  // 2. New research form
  assert.ok(html.includes('id="res-sec-new"'), 'New research form container');
  assert.ok(html.includes('id="res-input-topic"'), 'Topic input');
  assert.ok(html.includes('id="res-input-question"'), 'Question input');
  assert.ok(html.includes('id="res-select-mode"'), 'Mode select dropdown');
  assert.ok(html.includes('id="res-select-depth"'), 'Depth select dropdown');
  assert.ok(html.includes('id="res-range-max-sources"'), 'Max sources slider');
  assert.ok(html.includes('id="res-select-daterange"'), 'Date range filter');
  assert.ok(html.includes('id="res-chk-autoapprove"'), 'Auto-approve checkbox');
  assert.ok(html.includes('id="btn-start-research"'), 'Start research button');

  // 3. Research planner
  assert.ok(html.includes('id="res-sec-plan"'), 'Planner sub-section container');
  assert.ok(html.includes('id="res-plan-meta"'), 'Plan metadata label');
  assert.ok(html.includes('id="res-plan-main-q"'), 'Main research question');
  assert.ok(html.includes('id="res-plan-sub-q"'), 'Sub-questions list');
  assert.ok(html.includes('id="res-plan-objectives"'), 'Objectives list');
  assert.ok(html.includes('id="res-plan-queries-tbody"'), 'Planned queries table');
  assert.ok(html.includes('id="btn-approve-plan"'), 'Approve plan button');

  // 4. Sources & Retrieval
  assert.ok(html.includes('id="res-sec-sources"'), 'Sources container');
  assert.ok(html.includes('id="res-sources-container"'), 'Sources grid');
  assert.ok(html.includes('id="res-sources-count"'), 'Sources counter badge');

  // 5. Evidence Store
  assert.ok(html.includes('id="res-sec-evidence"'), 'Evidence container');
  assert.ok(html.includes('id="res-evidence-list"'), 'Evidence list container');
  assert.ok(html.includes('id="res-evidence-count"'), 'Evidence counter badge');

  // 6. Compare Sources
  assert.ok(html.includes('id="res-sec-compare"'), 'Compare sources container');
  assert.ok(html.includes('id="res-compare-matrix-box"'), 'Comparative matrix table box');
  assert.ok(html.includes('id="res-compare-proscons-box"'), 'Pros and cons box');

  // 7. Findings & Contradictions
  assert.ok(html.includes('id="res-sec-findings"'), 'Findings container');
  assert.ok(html.includes('id="res-contradictions-container"'), 'Contradictions list container');

  // 8. Final Report Viewer
  assert.ok(html.includes('id="res-sec-report"'), 'Report sub-section container');
  assert.ok(html.includes('id="res-report-heading"'), 'Report title heading');
  assert.ok(html.includes('id="res-report-content"'), 'Report body viewer');
  assert.ok(html.includes('onclick="readResearchSummaryAloud()"'), 'Read aloud action');
  assert.ok(html.includes('onclick="copyReportMarkdown()"'), 'Copy markdown action');
  assert.ok(html.includes("onclick=\"exportCurrentReport('markdown')\""), 'Download markdown');
  assert.ok(html.includes("onclick=\"exportCurrentReport('html')\""), 'Download html');
  assert.ok(html.includes("onclick=\"exportCurrentReport('json')\""), 'Download json');

  // 9. Saved Research Library
  assert.ok(html.includes('id="res-sec-library"'), 'Saved library container');
  assert.ok(html.includes('id="res-library-list"'), 'Saved library grid');

  // 10. Execution History & Logs
  assert.ok(html.includes('id="res-sec-history"'), 'History container');
  assert.ok(html.includes('id="res-history-container"'), 'History terminal logs');

  // 11. Settings
  assert.ok(html.includes('id="res-sec-settings"'), 'Settings container');
  assert.ok(html.includes('id="res-set-default-mode"'), 'Default mode setting');
  assert.ok(html.includes('id="res-set-max-sources"'), 'Default max sources setting');
  assert.ok(html.includes('id="res-set-auto-approve"'), 'Default auto approve setting');
});

test('client-side javascript functions for Research Assistant are declared', () => {
  assert.ok(html.includes('function switchResearchSection('), 'switchResearchSection defined');
  assert.ok(html.includes('async function startNewResearch('), 'startNewResearch defined');
  assert.ok(html.includes('function startResearchPolling('), 'startResearchPolling defined');
  assert.ok(html.includes('async function loadTaskPlan('), 'loadTaskPlan defined');
  assert.ok(html.includes('async function approveCurrentPlan('), 'approveCurrentPlan defined');
  assert.ok(html.includes('async function refreshTasksList('), 'refreshTasksList defined');
  assert.ok(html.includes('async function loadSavedReports('), 'loadSavedReports defined');
  assert.ok(html.includes('async function openReport('), 'openReport defined');
  assert.ok(html.includes('function exportCurrentReport('), 'exportCurrentReport defined');
  assert.ok(html.includes('function readResearchSummaryAloud('), 'readResearchSummaryAloud defined');
  assert.ok(html.includes('async function saveResearchSettings('), 'saveResearchSettings defined');
});
