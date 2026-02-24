# pingtest.py

import time
import ccxt
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

WORKERS = 60
PER_EXCHANGE_TIMEOUT = 10
CCXT_TIMEOUT_MS = 4000

ATTEMPTS = 5
SLEEP_BETWEEN = 0.25  # пауза между попытками


def probe_exchange(ex_id: str):
    ex = getattr(ccxt, ex_id)({
        "enableRateLimit": False,
        "timeout": CCXT_TIMEOUT_MS,
    })

    try:
        # только рабочие публичные методы
        if ex.has.get("fetchTime"):
            fn = ex.fetch_time
        elif ex.has.get("fetchStatus"):
            fn = ex.fetch_status
        else:
            return None  # игнорируем

        samples = []

        for i in range(ATTEMPTS):
            try:
                t0 = time.perf_counter()
                fn()
                dt = (time.perf_counter() - t0) * 1000
                samples.append(dt)
            except Exception:
                pass

            if i != ATTEMPTS - 1:
                time.sleep(SLEEP_BETWEEN)

        if not samples:
            return None

        # берём минимальный как самый близкий к реальному RTT
        best = min(samples)
        return (ex_id, best)

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
            try:
                r = fut.result(timeout=PER_EXCHANGE_TIMEOUT)
                if r is not None:
                    ok.append(r)
            except TimeoutError:
                pass
            except Exception:
                pass

    # сортировка по RTT (хуже сверху)
    ok.sort(key=lambda x: x[1], reverse=True)

    print(f"Measured exchanges: {len(ok)} | attempts: {ATTEMPTS}\n")
    print("RTT_ms   exchange")
    print("-" * 28)

    for ex_id, rtt in ok:
        print(f"{rtt:7.1f}  {ex_id}")


if __name__ == "__main__":
    main()