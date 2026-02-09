"""Run uvicorn server with Windows Proactor event loop fix for Playwright."""

import sys
import asyncio
import platform

# CRITICAL: Fix Playwright subprocess on Windows
# Must be set FIRST before any other imports
if platform.system() == 'Windows':
    # Force ProactorEventLoop policy for subprocess support (required by Playwright)
    policy = asyncio.WindowsProactorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)
    print(f"[run_server] Set event loop policy: {policy}")

import uvicorn

async def main():
    """Run uvicorn server with controlled event loop."""
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # MUST be False for Playwright to work on Windows
        workers=1,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    print(f"[run_server] Python version: {sys.version}")
    print(f"[run_server] Platform: {platform.system()}")

    if platform.system() == 'Windows':
        # Get the event loop from our policy
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print(f"[run_server] Event loop type: {type(loop).__name__}")

        try:
            loop.run_until_complete(main())
        finally:
            loop.close()
    else:
        # On Linux/Mac, just use asyncio.run()
        asyncio.run(main())
