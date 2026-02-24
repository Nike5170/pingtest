# pingtest.py
import time
import statistics
import ccxt
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

WORKERS = 60
PER_EXCHANGE_TIMEOUT = 10
CCXT_TIMEOUT_MS = 4000

ATTEMPTS = 5
SLEEP_BETWEEN = 0.25   # пауза между попытками, чтобы не ловить спайки/лимиты

def probe_exchange(ex_id: str):
    ex = getattr(ccxt, ex_id)({
        "enableRateLimit": False,
        "timeout": CCXT_TIMEOUT_MS,
    })

    try:
        if ex.has.get("fetchTime"):
            fn = ex.fetch_time
            method = "fetch_time"
        elif ex.has.get("fetchStatus"):
            fn = ex.fetch_status
            method = "fetch_status"
        else:
            return None  # нерабочие выкидываем

        samples = []
        for i in range(ATTEMPTS):
            t0 = time.perf_counter()
            try:
                fn()
                dt = (time.perf_counter() - t0) * 1000
                samples.append(dt)
            except Exception:
                pass

            # пауза между траями (кроме последнего)
            if i != ATTEMPTS - 1 and SLEEP_BETWEEN > 0:
                time.sleep(SLEEP_BETWEEN)

        if not samples:
            return None

        avg = statistics.fmean(samples)
        mn = min(samples)
        mx = max(samples)
        med = statistics.median(samples)
        return (ex_id, avg, mn, mx, med, len(samples), method)

    finally:
        try:
            ex.close()
        except Exception:
            pass

def main():
    ids = list(ccxt.exchanges)
    ok = []

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(probe_exchange, ex_id): ex_id for ex_id in ids}

        for fut in as_completed(futures):
            ex_id = futures[fut]
            try:
                r = fut.result(timeout=PER_EXCHANGE_TIMEOUT)
                if r is not None:
                    ok.append(r)
            except TimeoutError:
                pass
            except Exception:
                pass

    # сортировка по MIN (самый похожий на “пинг”), хуже сверху:
    ok.sort(key=lambda x: x[2], reverse=True)

    print(f"OK exchanges: {len(ok)} | attempts: {ATTEMPTS} | sleep: {SLEEP_BETWEEN}s\n")
    print("MIN_ms  MED_ms  AVG_ms  MAX_ms  ok/5  exchange           method")
    print("-" * 78)
    for ex_id, avg, mn, mx, med, n_ok, method in ok:
        print(f"{mn:6.1f} {med:6.1f} {avg:6.1f} {mx:6.1f}  {n_ok}/{ATTEMPTS}  {ex_id:<16} {method}")

if __name__ == "__main__":
    main()