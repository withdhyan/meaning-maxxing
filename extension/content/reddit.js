/**
 * Reddit platform adapter (new Reddit).
 */
MeaningFilter.Platform.register({
  selector: 'article, shreddit-post, [data-testid="post-container"]',

  getText(el) {
    const title = el.querySelector("a[slot='title'], h3, [data-testid='post-title']");
    const body = el.querySelector("[data-testid='post-body'], .md, p");
    let text = "";
    if (title) text += title.textContent + " ";
    if (body) text += body.textContent;
    return text.trim();
  },
});
