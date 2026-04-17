/**
 * YouTube platform adapter (home feed + search results).
 */
MeaningFilter.Platform.register({
  selector: "ytd-rich-item-renderer, ytd-video-renderer, ytd-compact-video-renderer",

  getText(el) {
    const title = el.querySelector("#video-title, #video-title-link");
    const channel = el.querySelector("#channel-name, .ytd-channel-name a");
    const meta = el.querySelector("#metadata-line, #description-text");
    let text = "";
    if (title) text += title.textContent + " ";
    if (channel) text += channel.textContent + " ";
    if (meta) text += meta.textContent;
    return text.trim();
  },
});
