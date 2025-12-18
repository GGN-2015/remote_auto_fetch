import hashlib
import os


def file_md5(file_path: str, chunk_size: int = 8192) -> str | None:
    """
    Calculate the MD5 hash value of a file
    :param file_path: Path to the target file
    :param chunk_size: Chunk size for reading the file (8KB by default, optimized for large files)
    :return: Returns 32-bit lowercase MD5 string if successful, None if failed
    """
    # Pre-check: Verify if the file exists and is a regular file
    if not os.path.exists(file_path):
        print(f"Error: File does not exist -> {file_path}")
        return None
    if not os.path.isfile(file_path):
        print(f"Error: Not a valid file -> {file_path}")
        return None

    try:
        # Initialize MD5 object
        md5_obj = hashlib.md5()
        
        # Read file in chunks (avoid memory overflow for large files)
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
        
        # Return 32-bit lowercase MD5 value
        return md5_obj.hexdigest().lower()
    
    except PermissionError:
        print(f"Error: No permission to read file -> {file_path}")
    except OSError as e:
        print(f"Error: Failed to read file -> {file_path} | Reason: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")
    
    return None
