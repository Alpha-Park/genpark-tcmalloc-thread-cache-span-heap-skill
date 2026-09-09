import sys
import json
from client import TCMallocThreadCache

tc = TCMallocThreadCache()

def handle_call(name, arguments):
    if name == "allocate":
        t = arguments.get("thread_id", "default")
        sz = arguments.get("size", 64)
        ptr = tc.allocate(t, sz)
        return {"pointer": ptr, "thread": t}
    elif name == "deallocate":
        t = arguments.get("thread_id", "default")
        ptr = arguments.get("pointer")
        sz = arguments.get("size", 64)
        tc.deallocate(t, tuple(ptr) if isinstance(ptr, list) else ptr, sz)
        return {"success": True}
    return {"error": f"Unknown tool: {name}"}

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            res = handle_call(req.get("name"), req.get("arguments", {}))
            print(json.dumps({"id": req.get("id"), "result": res}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
