"""Extract course PDFs and call the existing SMA AADGeneratorAgent."""

import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile

from autogen_agentchat.messages import TextMessage
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

from aad_prototype.generator import (
    build_generation_task,
    create_generator_agent,
    parse_generation_response,
)
from aad_prototype.pdf_extractor import extract_pdf


BASE_URL = os.getenv("ITI_LLM_BASE_URL", "https://iti-llm.insa-rouen.fr/v1")
MODEL = os.getenv("ITI_LLM_MODEL", "mistralai/Devstral-2-123B-Instruct-2512")
MAX_COURSE_CHARACTERS = 60000
SMA_CONFIG_PATH = Path(
    "/home/wissal/Téléchargements/SMA/aad_generation/config/m0.json"
)


def get_api_key():
    """Return the environment key or the key fixed in the local SMA config."""
    api_key = os.getenv("ITI_LLM_API_KEY")
    if api_key:
        return api_key

    if SMA_CONFIG_PATH.is_file():
        config = json.loads(SMA_CONFIG_PATH.read_text(encoding="utf-8"))
        api_key = config.get("api_key")
        if api_key:
            return api_key

    raise RuntimeError(
        "Clé API absente : renseignez api_key dans "
        f"{SMA_CONFIG_PATH} ou définissez ITI_LLM_API_KEY."
    )


async def generate(payload):
    api_key = get_api_key()

    excerpts = []
    with tempfile.TemporaryDirectory(prefix="aad-extraction-") as temp_dir:
        for index, source in enumerate(payload["pdf_paths"], start=1):
            source_path = Path(source)
            output_path = Path(temp_dir) / f"cours-{index}.txt"
            extract_pdf(source_path, output_path)
            excerpts.append(
                f"=== DOCUMENT {index}: {source_path.name} ===\n"
                f"{output_path.read_text(encoding='utf-8')}"
            )

    course_excerpt = "\n\n".join(excerpts)
    if len(course_excerpt) > MAX_COURSE_CHARACTERS:
        course_excerpt = course_excerpt[:MAX_COURSE_CHARACTERS]

    subject_id = payload["subject_id"]
    task = build_generation_task(
        chapter=f"Cours de {subject_id}",
        target_ac_id=f"COURS-{subject_id.upper()}",
        target_ac_title=(
            "Mobiliser de manière observable les notions et méthodes présentées "
            "dans le cours"
        ),
        course_excerpt=course_excerpt,
    )

    model_client = OpenAIChatCompletionClient(
        model=MODEL,
        base_url=BASE_URL,
        api_key=api_key,
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": ModelFamily.MISTRAL,
            "structured_output": False,
        },
    )
    try:
        agent = create_generator_agent(model_client)
        result = await agent.run(task=task)
        final_message = result.messages[-1]
        if not isinstance(final_message, TextMessage):
            raise TypeError("La réponse finale de l'agent n'est pas textuelle.")
        return parse_generation_response(final_message.content).model_dump()
    finally:
        await model_client.close()


def main():
    payload = json.load(sys.stdin)
    print(json.dumps(asyncio.run(generate(payload)), ensure_ascii=False))


if __name__ == "__main__":
    main()
