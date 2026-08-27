from requests.exceptions import HTTPError

from vlm_diagram_eval.parsing import graph as parser_service


def sanity_check(df_sanity, parser_service=parser_service, column="code"):
    """Process files to evaluate success, failures, and errors.

    Args:
        df_sanity: DataFrame containing the files to process.
        parser_service: Service to parse and evaluate the files.

    Returns:
        dict: A dictionary containing counts of successes, failures, errors, and error files.
    """
    success = 0  # Counter for successful generations
    fails = 0  # Counter for failed generations
    errors = 0  # Counter for HTTP errors
    error_files = []  # List to store indices of files with errors
    failed_filenames = []  # List to store image_filename of failed rows

    for i in range(len(df_sanity)):
        try:
            flag = parser_service.get_graph_from_json(df_sanity[column][i])
            if flag is None:
                fails += 1
                failed_filenames.append(df_sanity["image_filename"][i])  # Add failed filename
            else:
                success += 1  # Increment success counter if flag is not None
        except HTTPError as e:
            errors += 1  # Increment error counter for HTTP errors
            error_files.append(i + 1)  # Log the file index (1-based)
            print(f"HTTPError occurred for file {i + 1}: {e}")
        except Exception as e:
            errors += 1  # Increment error counter for other exceptions
            error_files.append(i + 1)  # Log the file index (1-based)
            print(f"An unexpected error occurred for file {i + 1}: {e}")

        print(f"Processed {i + 1} files")
        print(f"Total fails: {fails}")
        print(f"Total successes: {success}")
        print(f"Total errors: {errors}")

    return {
        "success": success,
        "fails": fails,
        "errors": errors,
        "error_files": error_files,
        "failed_filenames": failed_filenames,  # Return the list of failed filenames
    }
