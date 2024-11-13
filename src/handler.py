import os
import runpod
import json

from encryption_handler import EncryptionHandler
from utils import JobInput
from engine import vLLMEngine, OpenAIvLLMEngine

vllm_engine = vLLMEngine()
OpenAIvLLMEngine = OpenAIvLLMEngine(vllm_engine)


encryption_key = os.getenv("ENCRYPTION_KEY")
if encryption_key is None:
    encryption_handler = None
else:
    encryption_handler = EncryptionHandler(encryption_key)

async def handler(job):
    if encryption_handler is not None:
        prompt = job["input"].get('encrypted', False)

        if not prompt:
            yield {'error': 'Missing "encrypted" key in input!'}
            return

        prompt = json.loads(encryption_handler.decrypt(prompt))
    else:
        prompt = job["input"]

    job_input = JobInput(prompt)

    engine = OpenAIvLLMEngine if job_input.openai_route else vllm_engine
    results_generator = engine.generate(job_input)
    async for batch in results_generator:
        if encryption_handler is not None:
            yield {"encrypted": encryption_handler.encrypt(json.dumps(batch))}
        else:
            yield batch

runpod.serverless.start(
    {
        "handler": handler,
        "concurrency_modifier": lambda x: vllm_engine.max_concurrency,
        "return_aggregate_stream": True,
    }
)
