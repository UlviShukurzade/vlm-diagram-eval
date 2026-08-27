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
        {
            "role": "system",
            "content": "You are an expert system specialized in translating visual diagrams into clean, readable, and structurally perfect D2 (Declarative Diagramming) code. Your primary function is to analyze the components, containers, and relationships in an image and generate a D2 script that accurately represents this structure. Prioritize logical correctness , semantic clarity and precise syntax the highest priorities.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """


Your task is to create a syntactically perfect D2 script from the provided diagram.

## Strict Syntax Adherence
You **must** follow these core D2 syntax rules without deviation:
1.  **Node Definition:** `node_id: "Node Label"`
2.  **Container Definition:** `container_id: "Container Title" { ... }`
3.  **Connection to Nested Node:** `external_node_id -> container_id.internal_node_id`
4.  **Multi-line Text:** Must start with `|` on the first line and end with `|` on its own separate line.

## Process:
1.  **Analyze:** Identify all nodes and containers, determining what is inside and what is outside.
2.  **Assign IDs:** Assign a short, descriptive, snake_case ID to every node and container (e.g., `user_database`, `api_gateway`).
3.  **Construct Code in Order:** Write the script in this sequence:
    a. Define all **external** nodes.
    b. Define each container and all its **internal** nodes.
    c. Define all connections at the **end**.

## Crucial Example Pattern:
This example demonstrates the mandatory syntax and structure. Follow it precisely.
```d2
# External node definition
user: "External User"

# Container definition with an internal node
web_app: "Web Application" {
  # Note the multi-line text format
  api: |Internal API
    (REST)
  |
}

# Connection definition using container.node syntax
user -> web_app.api


            """,
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
    result = extract_mermaid_from_image("./numbered_mermaid_compatibles/46.png")
    print(result)
