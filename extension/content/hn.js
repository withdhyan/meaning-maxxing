/**
 * Hacker News platform adapter.
 */
MeaningFilter.Platform.register({
  selector: "tr.athing",

  getText(el) {
    const titleLink = el.querySelector(".titleline a");
    const subtext = el.nextElementSibling;
    let text = "";
    if (titleLink) text += titleLink.textContent;
    if (subtext) text += " " + subtext.textContent;
    return text.trim();
  },
});
