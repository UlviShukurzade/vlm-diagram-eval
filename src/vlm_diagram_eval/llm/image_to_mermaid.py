import base64
import os

from openai import AzureOpenAI

# Azure OpenAI client setup
client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
)


# Encode the image file to base64
def encode_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# Build a prompt that asks ONLY for Mermaid code extraction
def build_extraction_prompt(image_b64: str) -> list:
    return [
        {"role": "system", "content": "You are a diagram OCR assistant that extracts Mermaid.js code from images."},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Your primary goal is to translate the provided diagram into structurally perfect and semantically clear Mermaid.js code. Prioritize logical correctness and code readability over visual styling.\n\n## Instructions:\n1.  **Identify Core Elements:**\n    * Analyze the diagram's orientation (`LR` or `TD`).\n    * Identify all nodes, their text, and any container elements (subgraphs).\n\n2.  **Use Semantic Node IDs:**\n    * This is a critical rule. Instead of generic IDs like `A`, `B`, `C`, you **must** create short, descriptive, camelCase or snake_case IDs based on the node's primary content. For example, a node labeled 'Wheel Speed Sensor' should receive an ID like `wheelSpeedSensor` or `physics`.\n\n3.  **Define Structure and Boundaries:**\n    * Carefully distinguish between nodes inside a container and those outside.\n    * **Outside nodes** must be defined *outside* any `subgraph` block.\n    * **Inside nodes** must be defined *within* the `subgraph` block.\n\n4.  **Construct the Code Logically:**\n    * **Nodes First:** Define all nodes and subgraphs first.\n    * **Connections Last:** Define all connections (`---` or `-->`) at the end of the script, after all nodes and subgraphs have been declared. This is the cleanest and most reliable method.\n\n5.  **Format Text Accurately:**\n    * Transcribe all text literally, including `<<stereotypes>>`.\n    * Use the `<br>` tag to represent any multi-line text found within a node.\n\n## Output Constraints:\n* **Mermaid Code Only:** Your response must contain *only* the raw Mermaid code in a single Markdown block.\n* **Simple and Correct:** Do not add styling (`classDef`, `:::`) or layout renderers (`elk`). Focus only on generating the correct structure.",
                },
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            ],
        },
    ]


# Run GPT-4 Vision to extract code from the image
def extract_mermaid_from_image(image_path: str, model: str = "gpt-4.1-mini") -> str:
    image_b64 = encode_image_base64(image_path)
    messages = build_extraction_prompt(image_b64)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=2048,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    result = extract_mermaid_from_image("data/sample/48.png")
    print(result)
