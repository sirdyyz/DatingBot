class Metrics:
    def __init__(self):
        self.db_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.write_back_flushes = 0

    def reset(self):
        self.db_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.write_back_flushes = 0

    def get_stats(self):
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        return {
            "db_queries": self.db_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "write_back_flushes": self.write_back_flushes,
        }

metrics_store = Metrics()
