(() => {
  const selectors = [
    "[data-message-id] .a3s",
    ".adn .a3s",
    "[role='main'] [dir='ltr']",
    "[role='main']"
  ];

  for (const selector of selectors) {
    const node = document.querySelector(selector);
    const text = node?.innerText?.replace(/\s+/g, " ").trim();
    if (text && text.length > 30) {
      console.table([{ selector, characters: text.length, preview: text.slice(0, 160) }]);
      return text;
    }
  }

  console.warn("No Gmail email body selector matched.");
  return "";
})();
