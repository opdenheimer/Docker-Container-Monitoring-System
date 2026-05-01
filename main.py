import logging
from threading import Thread

from doctor.api.health import app
from doctor.core.monitor import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

if __name__ == "__main__":
    # Health endpoint runs in a background daemon thread
    flask_thread = Thread(
        target=lambda: app.run(host="0.0.0.0", port=8080, debug=False),
        daemon=True,
    )
    flask_thread.start()
    logging.getLogger(__name__).info("Health endpoint running on :8080")

    try:
        run()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Container Doctor shutting down.")
