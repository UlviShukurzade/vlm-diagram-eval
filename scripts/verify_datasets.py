"""
Dataset Verification Script

This script loads and verifies the newly created separated datasets.
"""

from datasets import load_from_disk


def verify_dataset(dataset_path, dataset_name):
    """Verify a dataset by loading and checking its structure."""
    print(f"\n🔍 Verifying {dataset_name}...")
    print(f"📂 Path: {dataset_path}")

    try:
        # Load dataset
        dataset = load_from_disk(dataset_path)

        print("✅ Dataset loaded successfully!")
        print(f"📊 Splits: {list(dataset.keys())}")

        for split_name in dataset.keys():
            split_data = dataset[split_name]
            print(f"📊 {split_name}: {len(split_data)} samples")

            # Convert to pandas for analysis
            df = split_data.to_pandas()

            # Check diagram types
            if "diagram_type" in df.columns:
                type_counts = df["diagram_type"].value_counts()
                print(f"🔍 Diagram types in {split_name}:")
                for dtype, count in type_counts.items():
                    percentage = (count / len(df)) * 100
                    print(f"  {dtype}: {count} ({percentage:.1f}%)")

            # Check difficulty distribution
            if "difficulty" in df.columns:
                diff_counts = df["difficulty"].value_counts()
                print(f"🎯 Difficulty levels in {split_name}:")
                for difficulty, count in diff_counts.items():
                    percentage = (count / len(df)) * 100
                    print(f"  {difficulty}: {count} ({percentage:.1f}%)")

        return True

    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return False


def main():
    """Main verification function."""
    print("=" * 60)
    print("DATASET VERIFICATION")
    print("=" * 60)

    datasets_to_verify = [
        ("/home/shu1abt/Desktop/pictureRepresentation/GraphFlowchartDataset", "Combined Graph & Flowchart Dataset"),
        ("/home/shu1abt/Desktop/pictureRepresentation/Separated_GraphDataset", "Graph Only Dataset"),
        ("/home/shu1abt/Desktop/pictureRepresentation/Separated_FlowchartDataset", "Flowchart Only Dataset"),
    ]

    success_count = 0
    for dataset_path, dataset_name in datasets_to_verify:
        if verify_dataset(dataset_path, dataset_name):
            success_count += 1
        print("-" * 40)

    print(f"\n✅ Verification complete: {success_count}/{len(datasets_to_verify)} datasets verified successfully!")


if __name__ == "__main__":
    main()
