import time

import torch
from transformers import AutoModelForCausalLM, AutoProcessor

model_name = "DAMO-NLP-SG/VideoLLaMA3-2B"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",
)
processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
video_path = "media/fall-01-cam0.mp4"
question = "Describe this video in detail."

# Video conversation
conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {
        "role": "user",
        "content": [
            {"type": "video", "video": {"video_path": video_path, "fps": 1, "max_frames": 128}},
            {"type": "text", "text": question},
        ],
    },
]

inputs = processor(conversation=conversation, return_tensors="pt")
inputs = {k: v.cuda() if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
if "pixel_values" in inputs:
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
output_ids = model.generate(**inputs, max_new_tokens=128)
response = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
print(response)


a = time.time()
inputs = processor(conversation=conversation, return_tensors="pt")
b = time.time()
inputs = {k: v.cuda() if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
if "pixel_values" in inputs:
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)
c = time.time()
output_ids = model.generate(**inputs, max_new_tokens=128)
d = time.time()
response = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
e = time.time()

print(f"time: {b-a}")
print(f"time: {c-b}")
print(f"time: {d-c}")
print(f"time: {e-d}")

print(response)
