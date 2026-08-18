export type NavigationCleanup = () => void;

const DEFAULT_POLL_INTERVAL_MS = 750;

export function watchProjectNavigation(
  onPotentialChange: () => void,
  pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
): NavigationCleanup {
  let lastUrl = window.location.href;
  const check = () => {
    const nextUrl = window.location.href;
    if (nextUrl === lastUrl) return;
    lastUrl = nextUrl;
    onPotentialChange();
  };

  const title = document.querySelector("title") ?? document.documentElement;
  const titleObserver = new MutationObserver(onPotentialChange);
  titleObserver.observe(title, { childList: true, subtree: true });

  const interval = window.setInterval(check, pollIntervalMs);
  window.addEventListener("popstate", check);
  window.addEventListener("hashchange", check);
  document.addEventListener("visibilitychange", check);

  return () => {
    titleObserver.disconnect();
    window.clearInterval(interval);
    window.removeEventListener("popstate", check);
    window.removeEventListener("hashchange", check);
    document.removeEventListener("visibilitychange", check);
  };
}
