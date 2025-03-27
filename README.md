# `k2 build` related
This is a workaround script to download missing files while using `k2 build`

## Issue
Discussed [HERE](https://github.com/DerrickWood/kraken2/issues/928)

While downloading files, `k2 build` skips some of the files and throws `FileNotFoundError` in the downstream process
```
FileNotFoundError: [Errno 2] No such file or directory: '/DBs/kraken/std_build/library/bacteria/genomes/all/GCF/000/003/215/GCF_000003215.1_ASM321v1/GCF_000003215.1_ASM321v1_genomic.fna'
```

## Workaround
`k2_get_missing_files.py` tries to download the missing file by using the **`manifest.txt`** file created while running `k2 build`  
It creates a list of downloaded `gz` files in the corresponding directories and compares with the list in manifest

### Usage

Example
```bash
$ python k2_get_missing_files.py -i /DBs/kraken/std_build/library/bacteria -t 20
```
Input path is the path to the manifest file

```
usage: k2_get_missing_files.py [-h] -i INPUT [-t [THREADS]]

Download missing files for Kraken 2 databases

options:
  -h, --help            show this help message and exit
  -i, --input INPUT     Path to the manifest file
  -t, --threads [THREADS]
                        Number of threads
```

It should work on manifest files generated for archaea, bacteria, human, and viral datasets