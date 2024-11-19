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
    print("Setup encryption handler with provided key")

async def handler(job):
    job_input = JobInput(job["input"])

    if encryption_handler is not None:
        # print("Got input", job["input"])

        if job_input.openai_route:
            prompt = job_input.openai_input["encrypted"]
        else:
            prompt = job["input"].get('encrypted', False)

        # print("Got prompt", prompt)
        if prompt is None:
            yield {'error': 'Missing "encrypted" key in input!'}
            return

        # print("Decoding", prompt)
        # print("Decoded", encryption_handler.decrypt(prompt))
        # print("Loading json")
        json_prompt = json.loads(encryption_handler.decrypt(prompt))
        # print("Decoded", json_prompt)

        if job_input.openai_route:
            job_input = JobInput({**job["input"], "openai_input": json_prompt})
        else:
            job_input = JobInput(json_prompt)

        # print("Reconstructed", job_input)


    engine = OpenAIvLLMEngine if job_input.openai_route else vllm_engine
    results_generator = engine.generate(job_input)
    async for batch in results_generator:
        # print("Got batch", batch)
        if encryption_handler is not None:
            encrypted_json = {"encrypted": encryption_handler.encrypt(json.dumps({"data": batch}))}
            if batch is str:
                yield json.dumps(encrypted_json) + "\n\n"
            else:
                yield encrypted_json
        else:
            yield batch

runpod.serverless.start(
    {
        "handler": handler,
        "concurrency_modifier": lambda x: vllm_engine.max_concurrency,
        "return_aggregate_stream": True,
    }
)
