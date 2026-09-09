import collections

class TCMallocThreadCache:
    """
    Thread-Caching Malloc (TCMalloc) model.
    Three-tier hierarchy:
    - Thread-Local Cache (zero lock contention for small objects)
    - Central Freelist (per-size class shared buffer)
    - Page Heap (manages spans of contiguous 4KB pages)
    """
    PAGE_SIZE = 4096
    SIZE_CLASSES = [8, 16, 32, 64, 128, 256, 512, 1024]

    def __init__(self):
        self.page_heap = PageHeap()
        self.central_freelists = {sc: [] for sc in self.SIZE_CLASSES}
        self.thread_caches = {}

    def register_thread(self, thread_id):
        self.thread_caches[thread_id] = {sc: [] for sc in self.SIZE_CLASSES}

    def allocate(self, thread_id, size):
        sc = next((s for s in self.SIZE_CLASSES if size <= s), None)
        if sc is None:
            pages = (size + self.PAGE_SIZE - 1) // self.PAGE_SIZE
            return self.page_heap.alloc_span(pages)

        tc = self.thread_caches.setdefault(thread_id, {s: [] for s in self.SIZE_CLASSES})
        if tc[sc]:
            return tc[sc].pop()

        batch = self._fetch_from_central(sc, batch_size=8)
        ret = batch.pop()
        tc[sc].extend(batch)
        return ret

    def deallocate(self, thread_id, ptr, size):
        sc = next((s for s in self.SIZE_CLASSES if size <= s), None)
        if sc is None:
            pages = (size + self.PAGE_SIZE - 1) // self.PAGE_SIZE
            self.page_heap.free_span(ptr, pages)
            return

        tc = self.thread_caches.setdefault(thread_id, {s: [] for s in self.SIZE_CLASSES})
        tc[sc].append(ptr)
        if len(tc[sc]) > 16:
            to_flush = tc[sc][:8]
            tc[sc] = tc[sc][8:]
            self.central_freelists[sc].extend(to_flush)

    def _fetch_from_central(self, sc, batch_size=8):
        c_list = self.central_freelists[sc]
        res = []
        while len(res) < batch_size and c_list:
            res.append(c_list.pop())
        if not res:
            span_id = self.page_heap.alloc_span(1)
            slots_count = self.PAGE_SIZE // sc
            for i in range(slots_count):
                res.append((span_id, sc, i))
        return res

class PageHeap:
    def __init__(self):
        self.next_span_id = 1
        self.free_spans = collections.defaultdict(list)

    def alloc_span(self, num_pages):
        if self.free_spans[num_pages]:
            return self.free_spans[num_pages].pop()
        sid = f"span_{self.next_span_id}"
        self.next_span_id += 1
        return sid

    def free_span(self, span_id, num_pages):
        self.free_spans[num_pages].append(span_id)
