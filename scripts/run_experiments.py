from pathlib import Path

import pandas as pd


def create_dataset_dataframe(dataset_path="Dataset_subset/Dataset_train"):
    """
    Create a pandas DataFrame from the dataset subset with image and mmd file pairs.

    Args:
        dataset_path (str): Path to the dataset folder

    Returns:
        pd.DataFrame: DataFrame with columns:
            - image_path: relative path to image file
            - mmd_path: relative path to corresponding mmd file
            - difficulty: encoded difficulty (1=Easy, 2=Moderate, 3=Hard, 0=undefined)
            - diagram_type: encoded diagram type (1=classDiagram, 2=flowchart, 3=graph, 4=stateDiagram, 0=undefined)
    """

    # Encoding mappings
    difficulty_mapping = {"Easy": 1, "Moderate": 2, "Hard": 3}

    diagram_type_mapping = {"classDiagram": 1, "flowchart": 2, "graph": 3, "stateDiagram": 4}

    data_rows = []

    # Walk through the image directory structure
    image_base = Path(dataset_path) / "image"
    code_base = Path(dataset_path) / "code"

    if not image_base.exists():
        raise FileNotFoundError(f"Image directory not found: {image_base}")

    # Process each diagram type
    for diagram_type_dir in image_base.iterdir():
        if not diagram_type_dir.is_dir():
            continue

        diagram_type = diagram_type_dir.name
        diagram_type_code = diagram_type_mapping.get(diagram_type, 0)

        # Process each difficulty level
        for difficulty_dir in diagram_type_dir.iterdir():
            if not difficulty_dir.is_dir():
                continue

            difficulty = difficulty_dir.name
            difficulty_code = difficulty_mapping.get(difficulty, 0)

            # Get all image files in this directory
            image_extensions = [".png", ".jpg", ".jpeg", ".svg"]

            for image_file in difficulty_dir.iterdir():
                if not image_file.is_file():
                    continue

                if image_file.suffix.lower() not in image_extensions:
                    continue

                # Get relative path from dataset root
                image_rel_path = str(image_file.relative_to(Path(dataset_path).parent))

                # Find corresponding mmd file
                base_name = image_file.stem
                mmd_file = code_base / diagram_type / difficulty / f"{base_name}.mmd"

                if mmd_file.exists():
                    mmd_rel_path = str(mmd_file.relative_to(Path(dataset_path).parent))

                    data_rows.append(
                        {
                            "image_path": image_rel_path,
                            "mmd_path": mmd_rel_path,
                            "difficulty": difficulty_code,
                            "diagram_type": diagram_type_code,
                        }
                    )
                else:
                    print(f"Warning: No corresponding mmd file found for {image_file}")

    # Create DataFrame
    df = pd.DataFrame(data_rows)

    # Sort by diagram_type, difficulty, then by filename for consistency
    df = df.sort_values(["diagram_type", "difficulty", "image_path"]).reset_index(drop=True)

    print(f"Created DataFrame with {len(df)} image-mmd pairs")
    print("Difficulty distribution:")
    print(df["difficulty"].value_counts().sort_index())
    print("Diagram type distribution:")
    print(df["diagram_type"].value_counts().sort_index())

    return df


def get_encoding_info():
    """
    Return the encoding mappings for reference.
    """
    return {
        "difficulty": {0: "undefined", 1: "Easy", 2: "Moderate", 3: "Hard"},
        "diagram_type": {0: "undefined", 1: "classDiagram", 2: "flowchart", 3: "graph", 4: "stateDiagram"},
    }


# Example usage
if __name__ == "__main__":
    # Create the dataframe
    df = create_dataset_dataframe()

    # Display sample data
    print("\nSample data:")
    print(df.head(10))

    # Save to CSV for later use
    df.to_csv("dataset_index.csv", index=False)
    print("\nDataFrame saved to dataset_index.csv")

    # Show encoding information
    print("\nEncoding mappings:")
    encodings = get_encoding_info()
    for key, mapping in encodings.items():
        print(f"{key}: {mapping}")
