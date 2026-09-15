/**
 * AGNI: Air-Gapped Neural Intelligence - Initial/Seed Data
 *
 * Empty on purpose: documents and chat history both start empty and are
 * populated entirely by real usage (uploads, and clicking "New Chat
 * Session"), persisted to localStorage from there by state.js. Keeping
 * this file (rather than inlining {documents:[], conversations:[]} into
 * state.js) preserves the seam for reintroducing demo/offline seed data
 * later without touching state.js itself.
 */

const MOCK_DATA = {
  INITIAL_DOCUMENTS: [],
  INITIAL_CONVERSATIONS: []
};

if (typeof window !== 'undefined') {
  window.MOCK_DATA = MOCK_DATA;
}
