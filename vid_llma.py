import os
import time

import dotenv
import torch
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from transformers import AutoModelForCausalLM, AutoProcessor

dotenv.load_dotenv()

# Tạo OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Thay bằng API key của bạn


# Hàm dịch tiếng Anh sang tiếng Việt nếu cần
def translate_to_vietnamese(text: str) -> str:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": "You are a professional translator."},
        {"role": "user", "content": f"Translate this text to Vietnamese:\n\n{text}"},
    ]

    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0)
    return response.choices[0].message.content.strip()


# Load model
model_name = "DAMO-NLP-SG/VideoLLaMA3-2B"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",
)
processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)

# Video & prompt bằng tiếng Anh
video_path = "media/fall-01-cam0.mp4"
question = """Analyze this video to detect human falls.
If a person is falling or has fallen, start your response with: "FALL_DETECTED:" followed by a detailed description of the situation (who, where, how).
If no fall is detected, respond with: "NO_FALL_DETECTED:" followed by a brief description of what is happening in the video."""

conversation = [
    {"role": "system", "content": "You are an AI system that specializes in fall detection. Analyze the video accurately and carefully."},
    {
        "role": "user",
        "content": [
            {"type": "video", "video": {"video_path": video_path, "fps": 1, "max_frames": 64}},
            {"type": "text", "text": question},
        ],
    },
]

# Xử lý input và đo thời gian
t0 = time.time()
inputs = processor(conversation=conversation, return_tensors="pt")
t1 = time.time()

inputs = {k: v.cuda() if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
if "pixel_values" in inputs:
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
t2 = time.time()

output_ids = model.generate(**inputs, max_new_tokens=128)
t3 = time.time()

response = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
t4 = time.time()

# In thời gian từng bước
print(f"[Preprocess time]: {t1 - t0:.2f} s")
print(f"[To CUDA time]: {t2 - t1:.2f} s")
print(f"[Generation time]: {t3 - t2:.2f} s")
print(f"[Decoding time]: {t4 - t3:.2f} s")

# In kết quả tiếng Anh
print(f"\n[Original Output]:\n{response}")

# Dịch sang tiếng Việt nếu cần
try:
    translated = translate_to_vietnamese(response)
    print(f"\n[Dịch sang tiếng Việt]:\n{translated}")
except Exception as e:
    print(f"\n[Lỗi khi dịch bằng OpenAI]: {e}")
