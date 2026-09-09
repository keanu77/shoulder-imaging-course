// Restore an explicit preference; first visits and unavailable storage stay dark.
(function () {
  document.documentElement.dataset.theme = "dark";
  try {
    var saved = localStorage.getItem("susc:theme");
    try { saved = JSON.parse(saved); } catch (error) {}
    if (saved === "light" || saved === "dark") {
      document.documentElement.dataset.theme = saved;
    }
  } catch (error) {}
})();
