// Scout bookmarklet source (posts to localhost only).
// Create a bookmark with URL:
// javascript:(()=>{...})();

(function () {
  try {
    const payload = {
      url: location.href,
      title: document.title,
      html: document.documentElement ? document.documentElement.outerHTML : '',
      text: document.body ? document.body.innerText : '',
    };

    fetch('http://127.0.0.1:5001/api/jd/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((j) => alert('Scout saved: ' + (j.path || 'ok')))
      .catch((e) => alert('Scout failed: ' + e.message));
  } catch (e) {
    alert('Scout failed: ' + e.message);
  }
})();
