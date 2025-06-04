import logging
import os
import time
from typing import Any, Dict, List

import cv2
import torch
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from transformers import AutoModelForCausalLM, AutoProcessor

logger = logging.getLogger(__name__)


class VideoLLamaFallDetector:
    """VideoLLaMA3-based fall detection system with OpenAI Vietnamese analysis"""

    def __init__(self, model_name="DAMO-NLP-SG/VideoLLaMA3-2B"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.is_loaded = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Initialize OpenAI client for Vietnamese analysis
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def translate_to_vietnamese_analysis(self, video_description: str) -> str:
        """Analyze video description and provide Vietnamese fall detection response"""
        try:
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": "Bạn là trợ lý AI chuyên về phát hiện té ngã trong môi trường bệnh viện."},
                {
                    "role": "user",
                    "content": f"""Hãy phân tích mô tả video này và xác định xem có xảy ra té ngã của con người hay không:
{video_description}

Chỉ trả lời theo một trong hai định dạng sau:
"PHÁT_HIỆN_TÉ_NGÃ: [mô tả ngắn gọn về té ngã]"
"KHÔNG_PHÁT_HIỆN_TÉ_NGÃ: [mô tả ngắn gọn về hoạt động bình thường]""",
                },
            ]

            response = self.openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0)
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error in OpenAI Vietnamese analysis: {e}")
            return f"LỖI_PHÂN_TÍCH: Không thể phân tích bằng OpenAI - {str(e)}"

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

    def get_video_description(self, frame_buffer: List[Dict]) -> str:
        """Get detailed video description from VideoLLaMA3 in English"""
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

            # Ask VideoLLaMA3 for detailed description in English
            question = """Describe this video in detail. Focus on:
            1. What people are doing in the video
            2. Any movements, actions, or activities
            3. Any falls, stumbles, or accidents
            4. Body positions and movements
            5. Environmental context

            Provide a comprehensive description of all activities and movements you observe."""

            conversation = [
                {
                    "role": "system",
                    "content": "You are an AI system that specializes in detailed video analysis. Analyze the video accurately and provide comprehensive descriptions.",
                },
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

            # Extract the actual response (remove conversation context) - with better error handling
            try:
                if "assistant\n\n" in response:
                    parts = response.split("assistant\n\n")
                    if len(parts) > 1:
                        response = parts[-1]
                elif "Assistant:" in response:
                    parts = response.split("Assistant:")
                    if len(parts) > 1:
                        response = parts[-1]
                elif "user" in response.lower() and "assistant" in response.lower():
                    # Try to find the last assistant response
                    lines = response.split("\n")
                    assistant_lines = []
                    found_assistant = False
                    for line in lines:
                        if "assistant" in line.lower():
                            found_assistant = True
                            continue
                        if found_assistant and line.strip():
                            assistant_lines.append(line)
                    if assistant_lines:
                        response = "\n".join(assistant_lines)
            except Exception as e:
                logger.warning(f"Error parsing response, using full response: {e}")
                # If parsing fails, just use the full response

            # Clean up response
            response = response.strip()

            # If response is empty or too short, return a default message
            if not response or len(response.strip()) < 10:
                response = "Video shows people in an indoor environment, but specific activities are unclear from the footage."

            analysis_time = time.time() - start_time
            logger.info(f"VideoLLaMA3 description completed in {analysis_time:.2f}s")

            # Clean up temp file
            try:
                import os

                os.remove(video_path)
            except:
                pass

            return response.strip()

        except Exception as e:
            logger.error(f"Error in VideoLLaMA3 video description: {e}")
            return f"DESCRIPTION_ERROR: {str(e)}"

    def analyze_frames(self, frame_buffer: List[Dict]) -> str:
        """Analyze frames for fall detection using VideoLLaMA3 + OpenAI flow"""
        if not self.is_loaded:
            logger.error("Model not loaded. Call load_model() first.")
            return "MODEL_NOT_LOADED"

        if not frame_buffer:
            logger.warning("Empty frame buffer")
            return "NO_FRAMES"

        try:
            # Step 1: Get detailed video description from VideoLLaMA3
            logger.info("Step 1: Getting video description from VideoLLaMA3...")
            video_description = self.get_video_description(frame_buffer)

            if video_description.startswith(("MODEL_NOT_LOADED", "NO_FRAMES", "FAILED_TO_CREATE_VIDEO", "DESCRIPTION_ERROR")):
                return video_description

            logger.info(f"VideoLLaMA3 description: {video_description}")

            # Step 2: Analyze description with OpenAI for Vietnamese fall detection
            logger.info("Step 2: Analyzing with OpenAI for Vietnamese fall detection...")
            vietnamese_analysis = self.translate_to_vietnamese_analysis(video_description)

            logger.info(f"Final Vietnamese analysis: {vietnamese_analysis}")

            return vietnamese_analysis

        except Exception as e:
            logger.error(f"Error in combined VideoLLaMA3+OpenAI analysis: {e}")
            return f"LỖI_PHÂN_TÍCH_KẾT_HỢP: {str(e)}"

    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        return {
            "loaded": self.is_loaded,
            "model_name": self.model_name,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "memory_allocated": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0,
            "memory_reserved": torch.cuda.memory_reserved() if torch.cuda.is_available() else 0,
            "openai_available": bool(os.getenv("OPENAI_API_KEY")),
        }
