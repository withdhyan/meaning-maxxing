/**
 * LinkedIn platform adapter.
 */
MeaningFilter.Platform.register({
  selector: ".feed-shared-update-v2, .occludable-update",

  getText(el) {
    const commentary = el.querySelector(".feed-shared-update-v2__description, .update-components-text");
    const reshared = el.querySelector(".feed-shared-article__description, .update-components-article__description");
    let text = "";
    if (commentary) text += commentary.textContent + " ";
    if (reshared) text += reshared.textContent;
    return text.trim();
  },
});
