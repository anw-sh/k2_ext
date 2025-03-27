#!/usr/bin/python

import argparse, glob, os, requests
import concurrent.futures
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException

def download_file(file, path):
    file_full_path = os.path.join(path_prefix, file)
    full_path = os.path.join(path_prefix, path)
    url = f"https://ftp.ncbi.nlm.nih.gov/{file}"

    os.makedirs(full_path, exist_ok=True)
    session = None
    try:
        # Session creation and adapter with retires
        session = requests.Session()
        retries = Retry(
            total = 3, 
            backoff_factor=1, 
            status_forcelist=[500, 502, 503, 504], 
            raise_on_status=False,
            allowed_methods=['HEAD', 'GET', 'OPTIONS']
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        if file_full_path not in downloaded_files:
            print(f"Downloading file: {file}...")

            response = session.get(url, timeout=10)
            response.raise_for_status()
            with open(file_full_path, "wb") as f:
                f.write(response.content)
            return f"Downloaded: {file}"
        else:
            # If file size comparison is required, execute the following lines
            # remote_file = requests.head(url)
            # remote_file.raise_for_status()
            # remote_size = int(remote_file.headers.get("Content-Length", 0))
            # local_size = os.path.getsize(file_full_path)
            # if local_size != remote_size:
            #     print(f"Re-downloading file: {file}")
            #     response = session.get(url, timeout=10)
            #     response.raise_for_status()
            #     with open(file_full_path, "wb") as f:
            #         f.write(response.content)
            #     return f"Re-downloaded: {file}"
            #     # os.system(f"curl {url} -o {file_full_path}")
            # else:
            return f"File already exists: {file}"
    except RequestException as e:
        print(f"Error downloading file: {file}: {e}")
        global errors
        errors.append(file)
        # exit(1)
    finally:
        if session is not None:
            session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download missing files for Kraken 2 databases")
    parser.add_argument("-i", "--input", help="Path to the manifest file", required=True)
    parser.add_argument("-t", "--threads", type=int, nargs="?", const=4, default=4, help="Number of threads")
    
    args = parser.parse_args()
    db_path = args.input
    threads = args.threads
    print("Provided path:", db_path)

    if db_path.endswith("/"):
        print("Trailing slash found in the given path, removing...")
        path_prefix = db_path.strip("/")
    else:
        print("No trailing slash found in the given path, continuing...")
        path_prefix = db_path
    print("Path:", path_prefix)

    req_dict = {}
    if "manifest.txt" in os.listdir(path_prefix):
        with open(f"{path_prefix}/manifest.txt") as f:
            for line in f:
                path = line.split("/")
                req_dict[line.strip()] = "/".join(path[:-1])
    else:
        print("The provided path does not contain the 'manifest.txt' file. Not proceeding further...")
        print("Manifest file can be found in the corresponding library directories like: ")
        print("'DBs/kraken/standard/library/bacteria/manifest.txt'")
        print("In such case, your input path should be 'DBs/kraken/standard/library/bacteria'")
        exit(1)
            
    print("\nNumber of genomes to download:", len(req_dict))

    downloaded_files = glob.glob(f"{path_prefix}/genomes/all/GCF/*/*/*/GCF*/*gz")
    downloaded_count = len(downloaded_files)
    print("Genomes missing:", len(req_dict) - downloaded_count)

    print(f"Using {threads} threads...")
    errors = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_file = {executor.submit(download_file, file, path): file for file, path in req_dict.items()}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result(timeout=30)
                print(result)
            except concurrent.futures.TimeoutError:
                print(f"Timeout occurred while processing {file}")
            except Exception as exc:
                print(f"An error occurred while processing {file}: {exc}")
                # exit(1)
    
    if not errors:
        print("Script has run without errors. Resume k2 build...")
    else:
        print(f"Script has run till the EOF, but there were {len(errors)} NCBI server errors...")
        print("Checking if the zip files are really missing...")
        no_zip = [error for error in errors if not glob.glob(f"{path_prefix}/{error}")]
        
        if not no_zip:
            print("Looks like, all zip files exist in their corresponding directories. Proceed with k2 build...")
        else:
            for idx, zip_file in enumerate(no_zip, start=1):
                print(f"Failed {idx}: {zip_file}")
            print("If the list is more, re-run the script, or else download manually...")