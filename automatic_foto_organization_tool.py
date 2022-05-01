"""
Created on Sat Apr 30 19:36:25 2022
"""

import os
import json
import re
from datetime import datetime
import sys
from tqdm import tqdm
import shutil


def initialize() -> dict:
    """
    Load the first found config file in subfolder "config"
    
    Parameters
    ----------
        
    Returns
    ------
    config: dict
        loaded configuration as dictionary
    """  
    # Load config from file
    base_path_file = os.path.dirname(__file__)
    config_path = os.path.join(base_path_file, "configs/")
    config_files_list = os.listdir(config_path) 
    
    for file in config_files_list:
        if file.endswith(".json"):
            filename = file
            break
    
    file_path = os.path.join(config_path, filename)
    try:
        with open(file_path, 'r') as file:
            txt = file.read()
            file.close()
    except:
        txt = None
    
    if txt is not None:
        config = json.loads(txt)
    else:
        print("The defined configuration files does not exist! Check spelling and start again!")
        return None
        
    return config


def get_all_files_from_source(src_path: str) -> list:
    """
    walks the given directory and lists all files with path in the given directory
    
    Parameters
    ----------
    src_path: str
        string to the directory
    
    Returns
    ------
    files: list
        list of all files in the given directory
    """
    files = []
    
    # get all files from source folder
    all_files_walk = []
    for root, dirs, files in os.walk(src_path, topdown=False):
       for name in files:
           path = os.path.join(root, name)
           all_files_walk.append(path)
       for name in dirs:
           path = os.path.join(root, name)
           all_files_walk.append(path)
    
    # filter to only have files
    files = []
    for file_path in all_files_walk:
    #    print(file_path)
        if os.path.isfile(file_path):
            files.append(file_path)

    return files


def get_size_of_directory(start_path: str) -> int:
    """
    Walks a path and adds the sizes of all directories to get the total size in bytes of the given path
    
    Parameters
    ----------
    start_path: str
        string with path to directory
    
    Returns
    ------
    total_size: int
        int showing the size of the directory in bytes
    """
    total_size = 0
    if not os.path.exists(start_path):
        return None
    
    for path, dirs, files in os.walk(start_path):
        for f in files:
            fp = os.path.join(path, f)
            total_size += os.path.getsize(fp)
    return total_size


def format_bytes(size: int) -> (int, str):
    """
    Formates the given size in bytes into power labes and rounds value in three digits
    
    Parameters
    ----------
    size: int
        int showing the size of a directory or file in bytes
    
    Returns
    ------
    new_size: int
        int showing the size of a directory or file rounded
    unit: str
        showing the new unit of the size with power label
    """
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'kilo', 2: 'mega', 3: 'giga', 4: 'tera'}
    try:
        while size > power:
            size /= power
            n += 1
            
        new_size = round(size, 3)
        unit = power_labels[n]+'bytes'
        return new_size, unit
    except Exception as e:
        print(e)
        return None, None
    

def filter_files_with_regex(files_list: list, filename_regex=r"") -> (list, list):
    """
    Splits list of input filenames into matching and non-matching with a regex.
    
    Parameters
    ----------
    files_list: list
        list of filename to be split up
    
    Returns
    ------
    imgs: list
        list of all files matching the regex
    others: list
        list of all files not matching the regex
    """
    imgs = []
    others = []
    
    filename_regex = r"(?P<filename>.*)\.(?P<extension>JPG|jpg|jpeg|PNG|png|tiff|tif|TIF|BMP|bmp)"
    
    for file in files_list:
        (path, image) = os.path.split(file)
        filename_matches = re.finditer(filename_regex, image, re.UNICODE)
        filename, extension = None, None
        for match in filename_matches:
            filename, extension = match.groups()
        if not filename or not extension:
            others.append(file)
            continue
        imgs.append(file)
    
    assert len(files_list) == (len(imgs) + len(others)), "Length of lists do not match!"
    
    return imgs, others


def process_images(imgs: list, config: dict):
    """
    

    Parameters
    ----------
    imgs : list
        DESCRIPTION.
    config : dict
        DESCRIPTION.

    Returns
    -------
    None.

    """
    start = datetime.now()
    success_list = []
    copy_list = []
    problem_list = []
    
    end = datetime.now()
    diff_time_seconds = (end - start).seconds
    return success_list, copy_list, problem_list, diff_time_seconds
 

def move_other_files(files: list, config: dict) -> (list, list, int):
    """
    Extracts the datatype of the files, creates folders and moves the files to its new directory
    
    Parameters
    ----------
    files: list
        list of paths to the other files
    config: dict
        loaded configuration as dictionary
    
    Returns
    ------
    success_files: list
        list of images that got moved successully
    problem_files: list
        list of images where a problem occured in the process
    diff_time_seconds: int
        measure how long this function needed to run in seconds
    """
    start = datetime.now()
    success_files = []
    problem_files = []
    
    sys.stdout.flush() # Force output of previous prints()
    for file in tqdm(files):
        (path, filename_full) = os.path.split(file)
        filename = filename_full.split('.')[0]
        extension = filename_full.split('.')[1]
        base_path = os.path.join(config["destination_path"], "Other Files", f"{extension}_Files")
        
        # Create base_path folder if not exists
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            
        dst_path = create_dst_path_for_file(base_path, filename, extension)
    
        # Move file to dst
        try:
            shutil.move(file, dst_path)
            success_files.append(file)
        except:
            problem_files.append(file)
            
    end = datetime.now()
    diff_time_seconds = (end - start).seconds
    
    return success_files, problem_files, diff_time_seconds


def create_dst_path_for_file(base_path, filename, extension):
    """
    A destination path is created with a given base, filename and extension. If the file already exists a copy label 
    will be included
    
    Parameters
    ----------
    base_path: str
        basic path of destination as string
    filename: str
        name of the file to be created as string
    extension: str
        extension of the file to be created as string
    
    Returns
    ------
    dst_path: str
        path including base, filename and extension as string
    """
    # Create base_path folder if not exists
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    # create dst file name and check if exists already
    created_filename = f"{filename}.{extension.lower()}"
    dst_path = os.path.join(base_path, created_filename)
    if os.path.exists(dst_path):
        good_to_go = False
        index = 0
        while good_to_go == False:
            index += 1
            created_filename = f"{filename}_Kopie({index}).{extension.lower()}"
            dst_path = os.path.join(base_path, created_filename)
            if not os.path.exists(dst_path):
                good_to_go = True
    
    return dst_path  
   

def main():
    """
    Main function, will call all necessary functions in the needed order
    
    Parameters
    ----------
    
    Returns
    ------
    results_dict: dict
        dictionary collecting all produced results
    """
    print("Welcome to the Foto Organization Tool!")
    config = initialize()
    results_dict = {}
    
    if config is not None:
        all_files_list = get_all_files_from_source(src_path=config["source_path"])
        src_size_bytes = get_size_of_directory(start_path=config["source_path"])
        src_size_format , src_size_unit = format_bytes(size=src_size_bytes)
        results_dict["all_files"] = {
                "all_files": all_files_list,
                "all_files_count": len(all_files_list),
                "dir_size": {"in_bytes": src_size_bytes,
                             "src_format": src_size_format,
                             "src_form_unit": src_size_unit
                             }
                }
        print(f"\nThe folder includes {len(all_files_list)} files which use {str(src_size_format)} {src_size_unit} of space.")
        
        images, other_files= filter_files_with_regex(files_list=all_files_list)
        results_dict["filter_with_regex"] = {
                "images": images,
                "imgages_count": len(images), 
                "other_files": other_files,
                "others_count": len(other_files)
                }
        print(f"The files are split in {len(images)} pictures and {len(other_files)} other files.")

        print("\nThe pictures will now be analyzed and moved. This could take some time ...")
        imgs_sucs, imgs_copy, imgs_prob, diff_time_exif = process_images(imgs=images, config=config) 
         
        results_dict["extract_exif_and_move"] = {
                "imgs_sucs": imgs_sucs,
                "imgs_copy": imgs_copy,
                "imgs_prob": imgs_prob,
                "diff_time_exif": diff_time_exif
                }
        
        if len(other_files) > 0:
            print("\n\nNow the no picture files will be sorted and moved. This could also take some time...")
            f_sucs, f_prob, moving_time = move_other_files(files=other_files, config=config)
            results_dict["moving_others"] = {
                    "f_sucs": f_sucs,
                    "f_prob": f_prob,
                    "moving_time": moving_time
                    }
    

        
    return results_dict


if __name__ == "__main__":
    results_dict = main()
