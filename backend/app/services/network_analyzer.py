import asyncio
from collections import defaultdict

# Example in-memory bandwidth tracker
bandwidth_data = defaultdict(lambda: {"upload": 0, "download": 0})

async def emit_bandwidth_loop(sio):
    while True:
        await asyncio.sleep(5)
        for user_id, usage in bandwidth_data.items():
            await sio.emit("network_stats", {
                "user_id": user_id,
                "upload_kb": usage["upload"] / 1024,
                "download_kb": usage["download"] / 1024
            })
