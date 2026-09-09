from client import TCMallocThreadCache

def main():
    print("=== Testing TCMalloc Thread Cache Hierarchy ===")
    tc = TCMallocThreadCache()
    tc.register_thread("worker-0")

    ptr1 = tc.allocate("worker-0", 32)
    print("Allocated 32B block:", ptr1)
    ptr2 = tc.allocate("worker-0", 32)
    print("Allocated second 32B block from thread-local cache:", ptr2)

    tc.deallocate("worker-0", ptr1, 32)
    reused = tc.allocate("worker-0", 32)
    print("Re-allocated 32B block (thread cache hit):", reused)
    assert reused == ptr1

    large_ptr = tc.allocate("worker-0", 16384)
    print("Direct PageHeap span allocation for large request:", large_ptr)
    assert str(large_ptr).startswith("span_")
    print("=== All tests passed successfully! ===")

if __name__ == "__main__":
    main()
