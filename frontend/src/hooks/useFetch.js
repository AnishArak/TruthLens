import { useCallback, useEffect, useRef, useState } from 'react'

/** Small data-loading hook: { data, error, loading, reload }. `fn` should be stable or wrapped in useCallback. */
export function useFetch(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const alive = useRef(true)

  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }))
    fn()
      .then((res) => alive.current && setState({ data: res.data ?? res, error: null, loading: false, meta: res }))
      .catch((err) => alive.current && setState({ data: null, error: err, loading: false }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    alive.current = true
    run()
    return () => {
      alive.current = false
    }
  }, [run])

  return { ...state, reload: run }
}
