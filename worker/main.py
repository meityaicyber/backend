import asyncio
import signal
import logging
import sys
from database import init_db, close_db
from processor import init_redis, close_redis
from consumer import consume_loop, stop_consumer
from prometheus_client import start_http_server

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    # Start Prometheus metrics server on port 8081
    start_http_server(8081)
    
    # Setup Signal Handlers for graceful shutdown (scaling/deployment)
    loop = asyncio.get_running_loop()
    
    def handle_sigterm():
        logging.info("Received termination signal. Shutting down gracefully...")
        stop_consumer()

    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGINT, handle_sigterm)
        loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
    
    # Initialize dependencies
    await init_db()
    await init_redis()

    try:
        # Start Kafka consumer loop (blocks until stop_consumer is called)
        await consume_loop()
    finally:
        # Cleanup
        await close_db()
        await close_redis()
        logging.info("Worker shutdown complete.")

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            # Windows doesn't support add_signal_handler for SIGINT/SIGTERM easily via asyncio,
            # so we catch KeyboardInterrupt in the execution wrapper.
            asyncio.run(main())
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        stop_consumer()
