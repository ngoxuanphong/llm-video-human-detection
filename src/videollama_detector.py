import logging
import time
from typing import Any, Dict, List

import cv2
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

logger = logging.getLogger(__name__)


class VideoLLamaFallDetector:
    """VideoLLaMA3-based fall detection system"""

    def __init__(self, model_name="DAMO-NLP-SG/VideoLLaMA3-2B"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.is_loaded = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Load the VideoLLaMA3 model and processor"""
        try:
            logger.info(f"Loading VideoLLaMA3 model: {self.model_name}")

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2",
            )

            self.processor = AutoProcessor.from_pretrained(self.model_name, trust_remote_code=True)

            self.is_loaded = True
            logger.info("VideoLLaMA3 model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load VideoLLaMA3 model: {e}")
            self.is_loaded = False
            return False

    def unload_model(self):
        """Unload the model to free memory"""
        try:
            if self.model:
                del self.model
                self.model = None
            if self.processor:
                del self.processor
                self.processor = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.is_loaded = False
            logger.info("VideoLLaMA3 model unloaded")

        except Exception as e:
            logger.error(f"Error unloading model: {e}")

    def create_video_file_from_frames(self, frame_buffer: List[Dict], temp_path: str = "temp_video.mp4") -> str:
        """Create a temporary video file from frame buffer"""
        try:
            if not frame_buffer:
                return None

            # Get video properties from first frame
            first_frame = frame_buffer[0]["frame"]
            height, width, _ = first_frame.shape

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            fps = 10  # 10 FPS for analysis
            out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

            # Write frames
            for frame_data in frame_buffer:
                out.write(frame_data["frame"])

            out.release()
            return temp_path

        except Exception as e:
            logger.error(f"Error creating video file: {e}")
            return None

    def analyze_frames(self, frame_buffer: List[Dict]) -> str:
        """Analyze frames for fall detection using VideoLLaMA3"""
        if not self.is_loaded:
            logger.error("Model not loaded. Call load_model() first.")
            return "MODEL_NOT_LOADED"

        if not frame_buffer:
            logger.warning("Empty frame buffer")
            return "NO_FRAMES"

        try:
            # Create temporary video file
            temp_video_path = "temp_analysis_video.mp4"
            video_path = self.create_video_file_from_frames(frame_buffer, temp_video_path)

            if not video_path:
                return "FAILED_TO_CREATE_VIDEO"

            # Prepare conversation for fall detection
            question = """Phân tích video này để phát hiện té ngã của con người.
            Nếu phát hiện thấy người té ngã, hãy trả lời bắt đầu với "PHÁT_HIỆN_TÉ_NGÃ:" theo sau là mô tả chi tiết về tình huống (người nào, ở đâu, như thế nào).
            Nếu không phát hiện té ngã, chỉ trả lời "KHÔNG_PHÁT_HIỆN_TÉ_NGÃ: [mô tả ngắn gọn những gì xảy ra trong video]"."""

            conversation = [
                {"role": "system", "content": "Bạn là một hệ thống AI chuyên phát hiện té ngã. Hãy phân tích video một cách chính xác và chi tiết."},
                {
                    "role": "user",
                    "content": [
                        {"type": "video", "video": {"video_path": video_path, "fps": 1, "max_frames": 64}},
                        {"type": "text", "text": question},
                    ],
                },
            ]

            # Process with VideoLLaMA3
            start_time = time.time()

            inputs = self.processor(conversation=conversation, return_tensors="pt")
            inputs = {k: v.cuda() if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

            if "pixel_values" in inputs:
                inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

            # Generate response
            output_ids = self.model.generate(**inputs, max_new_tokens=200)
            response = self.processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()

            # Extract the actual response (remove conversation context)
            if "assistant\n\n" in response:
                response = response.split("assistant\n\n")[-1]
            elif "Assistant:" in response:
                response = response.split("Assistant:")[-1]

            analysis_time = time.time() - start_time
            logger.info(f"VideoLLaMA3 analysis completed in {analysis_time:.2f}s: {response}")

            # Clean up temp file
            try:
                import os

                os.remove(video_path)
            except:
                pass

            return response.strip()

        except Exception as e:
            logger.error(f"Error in VideoLLaMA3 analysis: {e}")
            return f"ANALYSIS_ERROR: {str(e)}"

    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        return {
            "loaded": self.is_loaded,
            "model_name": self.model_name,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "memory_allocated": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0,
            "memory_reserved": torch.cuda.memory_reserved() if torch.cuda.is_available() else 0,
        }
