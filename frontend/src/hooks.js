import { useCallback, useEffect, useRef, useState } from "react";

/** Load data from the API; reload() refetches. pollMs > 0 refreshes in the background. */
export function useApi(loader, deps = [], pollMs = 0) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const reload = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const result = await loaderRef.current();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
    if (!pollMs) return undefined;
    const id = window.setInterval(() => reload(true), pollMs);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, loading, reload, setData };
}
