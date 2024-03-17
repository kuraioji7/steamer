from fastapi import FastAPI
import streamer_utils
from uvicorn import run
import os

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/updateGame")
def update_game_database():
    app_ids = streamer_utils.fetch_ids()
    streamer_utils.extraction_loop(app_ids, 500)
    return 200


@app.get("/resetGame")
def reset_game_data():
    return streamer_utils.reset_game_database()


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
