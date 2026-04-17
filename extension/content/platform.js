/**
 * Platform adapter interface.
 *
 * Each platform (twitter.js, reddit.js, etc.) registers an adapter that
 * knows how to find feed items and extract text from that platform's DOM.
 */

const MeaningFilter = window.MeaningFilter || {};
window.MeaningFilter = MeaningFilter;

MeaningFilter.Platform = {
  _adapter: null,

  register(adapter) {
    this._adapter = adapter;
    document.dispatchEvent(new CustomEvent("mf:platform-ready"));
  },

  /**
   * @returns {{ selector: string, getText: (el: Element) => string, getContainer: (el: Element) => Element }}
   */
  get() {
    return this._adapter;
  },
};
