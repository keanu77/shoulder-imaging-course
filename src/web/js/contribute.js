// Refresh the course/unit context at activation, including keyboard activation.
document.addEventListener("click", (event) => {
  const link = event.target.closest?.("a.ContributionLink");
  if (!link) return;
  const target = new URL(link.href);
  const context = new URL(target.searchParams.get("context"));
  context.hash = location.hash;
  const tab = new URLSearchParams(location.search).get("tab");
  if (tab && /^[a-z-]{1,30}$/.test(tab)) context.searchParams.set("tab", tab);
  target.searchParams.set("context", context.href);
  link.href = target.href;
});
