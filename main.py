"""Entry point for the Multi-Agent Travel Planning System."""
from ui.gradio import build_ui

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
