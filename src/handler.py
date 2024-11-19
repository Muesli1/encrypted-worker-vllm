import os
import runpod
import json

from encryption_handler import EncryptionHandler
from utils import JobInput
from engine import vLLMEngine, OpenAIvLLMEngine

vllm_engine = vLLMEngine()
OpenAIvLLMEngine = OpenAIvLLMEngine(vllm_engine)

# Prev worker: runpod/worker-v1-vllm:v1.2.0stable-cuda12.1.0

encryption_key = os.getenv("ENCRYPTION_KEY")
if encryption_key is None:
    encryption_handler = None
else:
    encryption_handler = EncryptionHandler(encryption_key)

async def handler(job):
    if encryption_handler is not None:
        prompt = job["input"].get('encrypted', False)

        print("Got input", job["input"])
        print("Got prompt", prompt)
        if prompt is None:
            yield {'error': 'Missing "encrypted" key in input!'}
            return

        print("Decoding", prompt)
        print("Decoded", encryption_handler.decrypt(prompt))
        print("Loading json")
        prompt = json.loads(encryption_handler.decrypt(prompt))
        print("Decoded", prompt)
    else:
        prompt = job["input"]

    job_input = JobInput(prompt)

    engine = OpenAIvLLMEngine if job_input.openai_route else vllm_engine
    results_generator = engine.generate(job_input)
    async for batch in results_generator:
        print("Got batch", batch)
        if encryption_handler is not None:
            yield {"encrypted": encryption_handler.encrypt(json.dumps({"data": batch}))}
        else:
            yield batch

runpod.serverless.start(
    {
        "handler": handler,
        "concurrency_modifier": lambda x: vllm_engine.max_concurrency,
        "return_aggregate_stream": True,
    }
)
