# rtt_whitebit.py
import time
import statistics
import ccxt

ATTEMPTS = 5
TIMEOUT_MS = 4000

def main():
    ex = ccxt.whitebit({
        "enableRateLimit": False,
        "timeout": TIMEOUT_MS,
    })

    samples = []

    for _ in range(ATTEMPTS):
        t0 = time.perf_counter()
        ex.fetch_time()          # публичный endpoint
        dt = (time.perf_counter() - t0) * 1000
        samples.append(dt)
        time.sleep(0.2)

    print("RTT samples (ms):", [round(x, 1) for x in samples])
    print("MIN:", round(min(samples), 1))
    print("MED:", round(statistics.median(samples), 1))
    print("AVG:", round(statistics.mean(samples), 1))
    print("MAX:", round(max(samples), 1))

if __name__ == "__main__":
    main()