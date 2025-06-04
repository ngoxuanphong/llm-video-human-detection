import os
import time

import dotenv
import torch
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from transformers import AutoModelForCausalLM, AutoProcessor

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def translate_to_vietnamese(text: str) -> str:
    """Analyze English video description and provide Vietnamese fall detection response"""
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": "Bạn là trợ lý AI chuyên về phát hiện té ngã trong môi trường bệnh viện."},
        {
            "role": "user",
            "content": f"""Hãy phân tích mô tả video này và xác định xem có xảy ra té ngã của con người hay không:
{text}

Chỉ trả lời theo một trong hai định dạng sau:
"PHÁT_HIỆN_TÉ_NGÃ: [mô tả ngắn gọn về té ngã]"
"KHÔNG_PHÁT_HIỆN_TÉ_NGÃ: [mô tả ngắn gọn về hoạt động bình thường]""",
        },
    ]

    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0)
    return response.choices[0].message.content.strip()


def load_model(model_name: str = "DAMO-NLP-SG/VideoLLaMA3-2B"):
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
    return model, processor


def get_video_description(model, processor, video_path: str):
    """Get detailed video description from VideoLLaMA3 in English"""
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

    inputs = processor(conversation=conversation, return_tensors="pt")
    inputs = {k: v.cuda() if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    if "pixel_values" in inputs:
        inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

    t2 = time.time()
    output_ids = model.generate(**inputs, max_new_tokens=200)
    t3 = time.time()

    response = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()

    # Extract the actual response (remove conversation context)
    if "assistant\n\n" in response:
        response = response.split("assistant\n\n")[-1]
    elif "Assistant:" in response:
        response = response.split("Assistant:")[-1]

    print(f"[VideoLLaMA3 Generation time]: {t3 - t2:.2f} s")

    return response.strip()


if __name__ == "__main__":
    video_path = "media/fall-01-cam0.mp4"
    model_name = "DAMO-NLP-SG/VideoLLaMA3-2B"

    print("🚀 Bắt đầu quá trình phân tích 2 bước:")
    print("📹 Step 1: VideoLLaMA3 sẽ mô tả video chi tiết")
    print("🤖 Step 2: OpenAI sẽ phân tích mô tả để phát hiện té ngã\n")

    # Load VideoLLaMA3 model
    print("⏳ Đang tải VideoLLaMA3 model...")
    model, processor = load_model(model_name)
    print("✅ VideoLLaMA3 model đã tải thành công!\n")

    # Step 1: Get video description from VideoLLaMA3
    print("📹 STEP 1: Lấy mô tả chi tiết từ VideoLLaMA3...")
    video_description = get_video_description(model, processor, video_path)
    print(f"📝 Mô tả video (VideoLLaMA3): {video_description}\n")

    # Step 2: Analyze with OpenAI for Vietnamese fall detection
    print("🤖 STEP 2: Phân tích mô tả bằng OpenAI để phát hiện té ngã...")
    vietnamese_analysis = translate_to_vietnamese(video_description)
    print(f"🏥 Kết quả phân tích (OpenAI Vietnamese): {vietnamese_analysis}\n")

    print("✅ Hoàn thành quá trình phân tích 2 bước!")
    print("💡 Ưu điểm: VideoLLaMA3 hiểu video tốt hơn, OpenAI phân tích ngôn ngữ tự nhiên tốt hơn")
