from meta_agent_app import create_app
from meta_agent_app.config import Settings


settings = Settings.load()
app = create_app(settings)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=18899, debug=settings.debug, use_reloader=False)
