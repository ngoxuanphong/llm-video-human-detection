import gradio as gr
import time
from datetime import datetime

def test_function():
    return f"Test successful! Time: {datetime.now().strftime('%H:%M:%S')}"

# Create a simple interface to test Gradio 5.x
with gr.Blocks(title="Test Gradio") as demo:
    gr.Markdown("# Gradio 5.x Test")
    
    output = gr.Textbox(label="Output", value=test_function())
    refresh_btn = gr.Button("Refresh")
    
    refresh_btn.click(test_function, outputs=[output])
    
    # Test the new timer functionality
    try:
        timer = gr.Timer(3.0)
        timer.tick(test_function, outputs=[output])
        print("✅ Timer works!")
    except Exception as e:
        print(f"❌ Timer error: {e}")
        # Fallback without timer
        pass

if __name__ == "__main__":
    print("🧪 Testing Gradio 5.x compatibility...")
    demo.launch(server_name="127.0.0.1", server_port=7861, share=False) 