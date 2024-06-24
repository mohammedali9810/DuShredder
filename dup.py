#### SEVENTH MOD ADD MEM USG & HANDLE LARGE FILES

import os
import hashlib
import json
import logging
import time
from datetime import datetime
import psutil

# Set up logging to output to both console and a file named 'output.log'
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('output.log')
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def hash_file(file_path, chunk_size=8192):
    """Generate a hash for a file using a specified chunk size for large files."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(chunk_size):
                hasher.update(chunk)
    except PermissionError:
        logger.info(f"Permission denied: {file_path}")
        return None, "PermissionError"
    except Exception as e:
        logger.info(f"Error reading file {file_path}: {e}")
        return None, str(e)
    return hasher.hexdigest(), None

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # Convert bytes to MB

def find_duplicate_files(directory):
    """Find and delete duplicate files in the specified directory."""
    file_hashes = {}
    errors = {}
    deleted_files = {}
    memory_usages = []
    
    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            mem_usage_before = get_memory_usage()
            file_hash, error = hash_file(file_path)
            mem_usage_after = get_memory_usage()
            memory_usages.append(mem_usage_after)

            logger.info(f"Memory usage before hashing {file_path}: {mem_usage_before:.2f} MB")
            logger.info(f"Memory usage after hashing {file_path}: {mem_usage_after:.2f} MB")
            
            if error:
                errors[file_path] = error
                continue
            
            if file_hash in file_hashes:
                logger.info(f"Deleting duplicate file: {file_path}")
                mem_usage_before = get_memory_usage()
                try:
                    os.remove(file_path)
                    deleted_files[file_path] = file_hash
                except PermissionError:
                    errors[file_path] = "PermissionError during deletion"
                except Exception as e:
                    errors[file_path] = f"Error during deletion: {str(e)}"
                mem_usage_after = get_memory_usage()
                memory_usages.append(mem_usage_after)
                logger.info(f"Memory usage before deleting {file_path}: {mem_usage_before:.2f} MB")
                logger.info(f"Memory usage after deleting {file_path}: {mem_usage_after:.2f} MB")
            else:
                file_hashes[file_hash] = file_path
    
    # Save errors and deleted files to JSON
    with open('errors.json', 'w') as error_file:
        json.dump(errors, error_file, indent=4)
    
    with open('deleted_files.json', 'w') as deleted_file:
        json.dump(deleted_files, deleted_file, indent=4)
    
    logger.info(f"Total files with errors: {len(errors)}")
    logger.info(f"Total duplicate files deleted: {len(deleted_files)}")

    average_memory_usage = sum(memory_usages) / len(memory_usages) if memory_usages else 0
    logger.info(f"Average memory usage: {average_memory_usage:.2f} MB")
    
    return errors, deleted_files, average_memory_usage

if __name__ == "__main__":
    start_time = time.time()
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Process start at: {start_time_str}")
    
    initial_memory_usage = get_memory_usage()
    logger.info(f"Initial memory usage: {initial_memory_usage:.2f} MB")

    directory_to_search = "M:/"  # Set this to the partition or directory to search
    
    errors, deleted_files, average_memory_usage = find_duplicate_files(directory_to_search)
    
    end_time = time.time()
    end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elapsed_time = end_time - start_time
    final_memory_usage = get_memory_usage()

    logger.info(f"Process end at: {end_time_str}")
    logger.info(f"Total time taken: {elapsed_time:.2f} seconds")
    logger.info(f"Final memory usage: {final_memory_usage:.2f} MB")
    
    # Add start and end times to the JSON data
    summary = {
        "start_time": start_time_str,
        "end_time": end_time_str,
        "elapsed_time": elapsed_time,
        "initial_memory_usage": initial_memory_usage,
        "final_memory_usage": final_memory_usage,
        "average_memory_usage": average_memory_usage,
        "errors": errors,
        "deleted_files": deleted_files
    }
    
    # Save the summary to a JSON file
    with open('summary.json', 'w') as summary_file:
        json.dump(summary, summary_file, indent=4)
    
    logger.info(f"Summary saved to summary.json")