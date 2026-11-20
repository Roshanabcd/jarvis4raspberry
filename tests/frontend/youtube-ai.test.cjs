const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const path = require('node:path');

const indexPath = path.resolve(__dirname, '../../apps/dashboard/static/index.html');
const html = fs.readFileSync(indexPath, 'utf8');

test('nav-youtube tab button exists with correct accessibility attributes', () => {
  assert.ok(html.includes('id="nav-youtube"'), 'nav-youtube button exists');
  assert.ok(html.includes('aria-controls="tab-youtube"'), 'aria-controls points to tab-youtube');
  assert.ok(html.includes('onclick="showTab(\'youtube\')"'), 'onclick calls showTab with youtube');
});

test('tab-youtube panel exists with tabpanel role and aria-labelledby', () => {
  assert.ok(html.includes('id="tab-youtube"'), 'tab-youtube container exists');
  assert.ok(html.includes('role="tabpanel"'), 'role="tabpanel" defined');
  assert.ok(html.includes('aria-labelledby="nav-youtube"'), 'aria-labelledby points to nav-youtube');
});

test('all 11 functional UI sections are present in tab-youtube', () => {
  // 1. Hero banner & telemetry
  assert.ok(html.includes('id="yt-status-pill"'), 'Status pill');
  assert.ok(html.includes('id="yt-api-badge"'), 'API badge');
  assert.ok(html.includes('id="yt-whisper-badge"'), 'Whisper badge');
  assert.ok(html.includes('id="yt-ffmpeg-badge"'), 'FFmpeg badge');

  // 2. Video input & SSRF feedback
  assert.ok(html.includes('id="yt-url-input"'), 'URL input');
  assert.ok(html.includes('id="yt-fetch-btn"'), 'Fetch button');
  assert.ok(html.includes('id="yt-url-feedback"'), 'Feedback box');

  // 3. Metadata card
  assert.ok(html.includes('id="yt-metadata-card"'), 'Metadata card');
  assert.ok(html.includes('id="yt-thumb-img"'), 'Thumbnail image');
  assert.ok(html.includes('id="yt-video-title"'), 'Video title');
  assert.ok(html.includes('id="yt-video-channel"'), 'Video channel');

  // 4. Authorized transcript management
  assert.ok(html.includes('id="yt-transcript-source-pill"'), 'Transcript source pill');
  assert.ok(html.includes('id="yt-subtitle-file-input"'), 'Subtitle file upload');
  assert.ok(html.includes('id="yt-media-path-input"'), 'Media path input');
  assert.ok(html.includes('id="yt-rights-confirm-checkbox"'), 'Rights confirmation checkbox');
  assert.ok(html.includes('id="yt-paste-transcript-text"'), 'Paste transcript text area');

  // 5. Transcript viewer
  assert.ok(html.includes('id="yt-transcript-list"'), 'Transcript list');
  assert.ok(html.includes('id="yt-transcript-search"'), 'Transcript search input');

  // 6. Multi-format summarizer (12 formats)
  const formats = ['quick', 'detailed', 'executive', 'key_points', 'chapters', 'concepts', 'action_items', 'study_notes', 'faq', 'revision', 'pros_cons', 'technical'];
  for (const fmt of formats) {
    assert.ok(html.includes(`id="yt-fmt-${fmt}"`), `Summary format button yt-fmt-${fmt} exists`);
  }
  assert.ok(html.includes('id="yt-summary-content"'), 'Summary content area');
  assert.ok(html.includes('onclick="saveCurrentYouTubeNote()"'), 'Save to Notes button');
  assert.ok(html.includes('onclick="readYouTubeSummaryAloud()"'), 'Read Aloud button');

  // 7. Chapters navigator
  assert.ok(html.includes('id="yt-chapters-list"'), 'Chapters list');
  assert.ok(html.includes('id="yt-chapters-count-badge"'), 'Chapters count badge');

  // 8. Key information & insights
  assert.ok(html.includes('id="yt-topics-tags"'), 'Topics tags');
  assert.ok(html.includes('id="yt-concepts-list"'), 'Concepts list');
  assert.ok(html.includes('id="yt-numbers-list"'), 'Dates and numbers list');

  // 9. Conversational "Ask This Video" Assistant
  assert.ok(html.includes('id="yt-ask-input"'), 'Ask input');
  assert.ok(html.includes('id="yt-ask-btn"'), 'Ask button');
  assert.ok(html.includes('id="yt-answer-card"'), 'Answer card');
  assert.ok(html.includes('id="yt-answer-grounding"'), 'Grounding pill');
  assert.ok(html.includes('id="yt-answer-timestamp"'), 'Timestamp pill');

  // 10. Saved notes library
  assert.ok(html.includes('id="yt-notes-list"'), 'Notes list');
  assert.ok(html.includes('id="yt-notes-search"'), 'Notes search');

  // 11. Activity history
  assert.ok(html.includes('id="yt-history-tbody"'), 'History table body');
  assert.ok(html.includes('onclick="clearYouTubeHistory()"'), 'Clear history button');
});

test('showTab contains youtube routing handler', () => {
  assert.ok(html.includes("if (name === 'youtube') { loadYouTubeCenter(); }"), 'showTab routes to loadYouTubeCenter()');
});

test('javascript functions are defined for all user interactions', () => {
  const fns = [
    'async function loadYouTubeCenter()',
    'async function validateAndFetchYouTubeVideo()',
    'async function checkAndLoadYouTubeTranscript(',
    'function renderTranscriptSegments(',
    'function filterTranscriptViewer()',
    'function copyYouTubeTranscript()',
    'function downloadYouTubeTranscript()',
    'function seekYouTubeTimestamp(',
    'async function uploadYouTubeSubtitleFile()',
    'async function submitPastedTranscript()',
    'async function transcribeLocalMediaFile()',
    'function selectYouTubeSummaryType(',
    'async function generateYouTubeSummary()',
    'function renderYouTubeChapters(',
    'function renderYouTubeKeyInfo(',
    'async function askYouTubeVideo()',
    'async function saveCurrentYouTubeNote()',
    'async function loadYouTubeNotes()',
    'async function exportYouTubeNote(',
    'async function deleteYouTubeNote(',
    'async function loadYouTubeHistory()',
    'async function clearYouTubeHistory()',
    'function readYouTubeSummaryAloud()',
  ];

  for (const fn of fns) {
    assert.ok(html.includes(fn), `Function '${fn}' is defined in index.html`);
  }
});
