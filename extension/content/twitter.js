/**
 * Twitter/X platform adapter.
 */
MeaningFilter.Platform.register({
  selector: 'article[data-testid="tweet"]',

  getText(el) {
    const tweetText = el.querySelector('[data-testid="tweetText"]');
    const userName = el.querySelector('[data-testid="User-Name"]');
    let text = "";
    if (userName) text += userName.textContent + " ";
    if (tweetText) text += tweetText.textContent;
    return text.trim();
  },
});
