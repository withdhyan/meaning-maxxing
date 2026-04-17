/**
 * Score text against user's attention policies.
 *
 * Two modes:
 *   1. Local (default): keyword overlap between policy words and post text.
 *      Fast, free, runs on every post. Good enough for filtering.
 *   2. LLM (optional): sends text + policies to Claude API via background
 *      worker for deeper semantic scoring. Used for borderline posts.
 *
 * Scoring produces a value between 0 (irrelevant) and 1 (deeply aligned).
 */

const MeaningFilter = window.MeaningFilter || {};
window.MeaningFilter = MeaningFilter;

MeaningFilter.Scorer = (() => {
  const STOPWORDS = new Set(
    "a an the that this these those of in to for with from by on at is are " +
    "was were be been being have has had do does did will would shall should " +
    "may might can could and but or nor not no so yet also very i me my we " +
    "our you your he she it they them their its just like get got how what " +
    "who when where why which all any some more most other than too up out " +
    "about into over after before between through during".split(" ")
  );

  let _policyWords = new Set();
  let _policyPhrases = [];

  function _tokenize(text) {
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, " ")
      .split(/\s+/)
      .filter((w) => w.length > 2 && !STOPWORDS.has(w));
  }

  function _extractPolicyWords(policies) {
    const words = new Set();
    const phrases = [];
    for (const policy of policies) {
      // Strip CAPITALIZED prefix
      const cleaned = policy.replace(/^[A-Z][A-Z\s]+\b/, "").trim();
      phrases.push(cleaned.toLowerCase());
      for (const w of _tokenize(cleaned)) {
        words.add(w);
      }
    }
    return { words, phrases };
  }

  /**
   * Load values from chrome.storage and build word index.
   */
  async function init() {
    return new Promise((resolve) => {
      chrome.storage.local.get(["values"], (result) => {
        const values = result.values || [];
        const allPolicies = values.flatMap((v) => v.policies || []);
        const { words, phrases } = _extractPolicyWords(allPolicies);
        _policyWords = words;
        _policyPhrases = phrases;
        resolve();
      });
    });
  }

  /**
   * Score a piece of text against loaded policies.
   *
   * Returns { score: 0-1, matchedWords: string[] }
   */
  function score(text) {
    if (_policyWords.size === 0) {
      return { score: 0, matchedWords: [] };
    }

    const textWords = new Set(_tokenize(text));
    const matchedWords = [];

    for (const pw of _policyWords) {
      if (textWords.has(pw)) {
        matchedWords.push(pw);
      }
    }

    // Word overlap score
    const wordScore = matchedWords.length / _policyWords.size;

    // Phrase proximity bonus: check if any policy phrase appears as substring
    const textLower = text.toLowerCase();
    let phraseBonus = 0;
    for (const phrase of _policyPhrases) {
      // Check for 3+ word subsequences from the phrase
      const phraseWords = phrase.split(/\s+/).filter((w) => w.length > 2 && !STOPWORDS.has(w));
      if (phraseWords.length < 2) continue;

      let consecutive = 0;
      for (const pw of phraseWords) {
        if (textLower.includes(pw)) {
          consecutive++;
        }
      }
      const phraseOverlap = consecutive / phraseWords.length;
      if (phraseOverlap > 0.5) {
        phraseBonus = Math.max(phraseBonus, phraseOverlap * 0.3);
      }
    }

    const finalScore = Math.min(1.0, wordScore + phraseBonus);
    return { score: finalScore, matchedWords };
  }

  /**
   * Classify a score into a bucket for CSS.
   */
  function classify(score) {
    if (score >= 0.15) return "resonant";
    if (score >= 0.05) return "neutral";
    return "dim";
  }

  return { init, score, classify };
})();
