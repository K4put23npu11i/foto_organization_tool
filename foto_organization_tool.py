"""
Inspired by ct.de/wtnz
"""

import logging
from datetime import datetime
from tqdm import tqdm
from PIL import Image
from PIL.ExifTags import TAGS
import shutil
import re
import json
import os
import sys


# Configure logging
easy_logging = True
if easy_logging is True:
    # Configure logging
    logger = logging.getLogger()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s - %(funcName)s: %(message)s")
else:
    logger = logging.getLogger()
    # create file handler which logs even debug messages
    fh = logging.FileHandler(str(__file__.split('/')[-1].split('.')[0]) + '.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s [%(module)s, %(funcName)s]: %(message)s', "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

# Measure running time:
start_time = datetime.now()
logger.info('Script started successfully!')


def initialize() -> dict:
    """
    Load the config file, ask for user approval and prepare everything
    
    Parameters
    ----------
        
    Returns
    ------
    config: dict
        loaded configuration as dictionary
    """
        
    # Load config from file
    config_path = "configs/"
    config_files_list = os.listdir(config_path)
    header_mes = "Following configuration files found:"
    filename = await_user_input_from_list_decision(list_to_decide=config_files_list, header_message=header_mes)
    
    if filename is None:
        return None
    
    file_path = os.path.join(config_path, filename)
    logger.debug(f"Read txt from json file. Filename: {file_path}")
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

    config_approval_message = "Following configuration is loaded:\n\n" + json.dumps(config, indent=4) + \
        "\n\nAre you fine with that?\nPlease press 'y' for approval or 'n' to stop the programm and start again.\n"
    
    user_approval = await_user_input(message=config_approval_message, allowed_answers=["y", "n"])
    
    if user_approval == "n":
        config = None
        
    return config


def await_user_input_from_list_decision(list_to_decide: list, header_message: str="") -> str:
    """
    Print message and wait for user input. Let the user choose from a given list of choices.
    !! Calls the function >await_user_input()< !!
    
    Parameters
    ----------
    list_to_decide: list
        list of allowed answers.
    header_message: str
        string that will be printed as question for user input
    
    Returns
    ------
    user_decision: str
        string of users input
    """
    user_decision = None
    
    if type(list_to_decide) is not list or len(list_to_decide) == 0:
        return None
    
    if len(list_to_decide) == 1:
        user_decision = list_to_decide[0]
        
    else:
        indexes = list(range(0, len(list_to_decide)))
        sorted_list = sorted(list_to_decide)
        message_str = header_message + "\n"
        for idx in range(0, len(list_to_decide)):
            number_str = f"{idx}\t: {sorted_list[idx]}\n"
            message_str += number_str
        
        message_str += "\nSelect a number to choose a value:\n"
        user_input = await_user_input(message=message_str, allowed_answers=indexes)
        user_decision = sorted_list[int(user_input)] 
    
    return user_decision


def await_user_input(message: str, allowed_answers: list = None) -> str:
    """
    Print message and wait for user input. Checks the input if allowed answers are specified.
    
    Parameters
    ----------
    message: str
        string that will be printed as question for user input
    allowed_answers: list
        list of allowed answers. Input will not be checked if not specified
    
    Returns
    ------
    user_input: str
        string of users input
    """
    allowed_answers_str_list = []
    if allowed_answers is not None:
        for element in allowed_answers:
            allowed_answers_str_list.append(str(element))
    logging.debug(f"Ask for approval for message: {message}")
    user_input = ""
    good_to_go = False
    while good_to_go != True:
        inp = str(input(message))
        
        if allowed_answers is not None:
            if inp in allowed_answers_str_list:
                user_input = inp
                good_to_go = True
            else:
                print("\nGiven input is not in allowed answers. Try again please.")
                print("Allowed answers are: " + str(allowed_answers_str_list))
        else:
            user_input = inp
            good_to_go = True
    
    logging.debug(f"User input of approval: {user_input}")
    
    return user_input


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
    while size > power:
        size /= power
        n += 1
        
    new_size = round(size, 3)
    unit = power_labels[n]+'bytes'
    return new_size, unit


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


def extract_exif_from_image_and_move_to_dest_folder(imgs: list, config: dict) -> (list, list, list, int):
    """
    Extracts the needed information of the photos, creates the corresponding destination path and moves the file 
    to its new direction. Creates lists to follow the process.
    
    Parameters
    ----------
    imgs: list
        list of paths to the pictures
    config: dict
        loaded configuration as dictionary
    
    Returns
    ------
    success_list: list
        list of images that got moved successully
    copy_list: list
        list of images that got moved successully and has the label "Kopie" in its name
    problem_list: list
        list of images where a problem occured in the process
    diff_time_seconds: int
        measure how long this function needed to run in seconds
    """
    start = datetime.now()
    success_list = []
    copy_list = []
    problem_list = []
    
    # unpack config
    output_folder = config["destination_path"]
    if str(config["include_year_in_destination_folder_level"]).lower() in ["true"]:
        include_year = True
    else: 
        include_year = False 
    
    sys.stdout.flush() # Force output of previous prints()
    # loop over images
    for image_path in tqdm(imgs):
#        print(image_path)
        try:
            image = Image.open(image_path)
            exifdata = image._getexif()
            image.close()
            exif_dict = {}
            for tag_id in exifdata:
                # get the tag name, instead of human unreadable tag id
                tag = TAGS.get(tag_id, tag_id)
                data = exifdata.get(tag_id)
                # decode bytes 
                if isinstance(data, bytes):
                    data = data.decode()
                exif_dict[tag] = data
            image_time = datetime.strptime(exif_dict["DateTime"], "%Y:%m:%d %H:%M:%S")
            year_str = image_time.strftime("%Y")
            year_month_str = image_time.strftime("%Y_%m")
            
            filename = f"IMG_{image_time.strftime('%Y%m%d')}_{image_time.strftime('%H%M%S')}"
            extension = image.format.lower()
            valid_exif = True
            
        except:
            image.close()
            (path, filename_full) = os.path.split(image_path)
            filename = filename_full.split('.')[0]
            extension = filename_full.split('.')[1]
            valid_exif = False
            
        
        # define new path for picture
        if valid_exif is True and include_year is True:
            base_path = os.path.join(output_folder, year_str, year_month_str)
            
        elif valid_exif is True and include_year is False:
            base_path = os.path.join(output_folder, year_month_str)
            
        else: # valid_exif is False
            base_path = os.path.join(output_folder, "No_exif_data")

        dst_path = create_dst_path_for_file(base_path, filename, extension)
                    
        # Move image to dst
        try:
            shutil.move(image_path, dst_path)
            success_list.append(dst_path)
            if "Kopie" in dst_path:
                copy_list.append(dst_path)
        except:
            problem_list.append(image_path)
            
    assert len(imgs) == len(success_list) + len(problem_list), "Lengths of lists do not match!"
    
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


def delete_empty_folders(directory: str, levels: int =10):
    """
    Loop over given directory and delete empty folders
    
    Parameters
    ----------
    directory: str
        base path to loop through
    levels: int
        amount of iterations, equals the level of directories topdown
    
    Returns
    ------

    """
    for i in range(0, levels):
        for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
            if not dirnames and not filenames and dirpath != directory:
                os.rmdir(dirpath)


def delete_copy_pictures_from_destination(config: dict) -> (list, list):
    """
    Loop over destination directory and collect all files with "Kopie" in it. Compare these file with the original and
    delete the copy if the sizes match.
    
    Parameters
    ----------
    dconfig: dict
        loaded configuration as dictionary, for the destination path
    
    Returns
    ------
    deleted_files: list
        files that where deleted successfully
    problem_files: list
        files that could not be deleted
    """
    sys.stdout.flush() # Force output of previous prints()
    path = config["destination_path"]
    
    # get all files in destination folder
    all_files = get_all_files_from_source(src_path=path)
    
    # get files with copies
    quene = []
    for file in all_files:
        if "Kopie" in file and os.path.isfile(file):
            quene.append(file)
    
    problem_files = []
    deleted_files = []
    for file in tqdm(quene):
        if os.path.isfile(file):
            org_file = file.split("Kopie")[0][:-1] + "." + file.split(".")[-1]
            size_org_file = os.path.getsize(org_file)
            size_file = os.path.getsize(file)
            
            if size_file == size_org_file:
                deleted_files.append(file)
            else:
                problem_files.append((file, "Size does not match"))
        else:
            problem_files.append((file, "No file"))
                
    counter = 0
    del_files = deleted_files.copy()
    while len(del_files) > 0 or counter < 10:
        counter += 1
        for file in del_files:
            if os.path.exists(file):
                os.remove(file)
            else:
                del_files.remove(file)
    
    if len(del_files) > 0:
        for file in del_files:
            problem_files.append((file, "Could not be deleted"))
            
    assert len(quene) == len(deleted_files) + len(problem_files), "Length of delete lists do not match"
            
    return deleted_files, problem_files


def final_comprehention_and_print_message(config: dict, results_dict: dict):
    """
    Builds the final print message to show performace statistics and kpis
    
    Parameters
    ----------
    config: dict
        loaded configuration as dictionary
    results_dict: dict
        collected information about process in previous functions
    
    Returns
    ------
    
    """
    sys.stdout.flush() # Force output of previous prints()
    mes = "\n\n\n-----  YEAH DONE  -----\n"
    
    mes += f"\nIn total {results_dict['all_files']['all_files_count']} elements where found in the source folder "
    mes += f"({results_dict['filter_with_regex']['imgages_count']} pictures, {results_dict['filter_with_regex']['others_count']} other files)\n"
    
    mes += f"\nSource-Path: {config['source_path']}\nDestination-Path: {config['destination_path']}\n"
    
    # Info about deleted files
    if str(config["delete_copy_pictures"]).lower() in ["true"]:
        mes += f"\nIn total {len(results_dict['delete_copy']['deleted_pictures'])} files where deleted, because they are duplicates.\n"
        mes += f"This deletion saves {results_dict['delete_copy']['size_diff']['size_diff_number']} {results_dict['delete_copy']['size_diff']['size_diff_unit']} in space.\n"
    
    print(mes)
    return None

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
        imgs_sucs, imgs_copy, imgs_prob, diff_time_exif = extract_exif_from_image_and_move_to_dest_folder(imgs=images, 
                                                                                                          config=config)
        results_dict["extract_exif_and_move"] = {
                "imgs_sucs": imgs_sucs,
                "imgs_copy": imgs_copy,
                "imgs_prob": imgs_prob,
                "diff_time_exif": diff_time_exif
                }
        
        print("\n\nNow the no picture files will be sorted and moved. This could also take some time...")
        f_sucs, f_prob, moving_time = move_other_files(files=other_files, config=config)
        results_dict["moving_others"] = {
                "f_sucs": f_sucs,
                "f_prob": f_prob,
                "moving_time": moving_time
                }
        
        print("\n\n\nDelete empty folders now ...")
        if str(config["delete_empty_source"]).lower() in ["true"]:
            delete_empty_folders(directory=config["source_path"])
            
        if str(config["delete_copy_pictures"]).lower() in ["true"]:
            print("\n\nDelete copy pictures now ...")
            size_before = get_size_of_directory(start_path=config["destination_path"])
            deleted_pictures, problem_pictures = delete_copy_pictures_from_destination(config=config)
            size_after = get_size_of_directory(start_path=config["destination_path"])
            size_diff_form, size_diff_unit = format_bytes(size=(size_before-size_after))
        else: 
            deleted_pictures, problem_pictures = (None, None)
            size_diff_form, size_diff_unit = (None, None)
        results_dict["delete_copy"] = {
                "deleted_pictures": deleted_pictures,
                "problem_pictures": problem_pictures,
                "size_diff": {
                        "size_diff_number": size_diff_form,
                        "size_diff_unit": size_diff_unit
                        }
                }
            
        final_comprehention_and_print_message(config=config, results_dict=results_dict)
        
        
    else:
        print("Please check your configuration and start again!")
        
    return results_dict


if __name__ == "__main__":
    results_dict = main()
    

# Measure running time:
end_time = datetime.now()
logger.info('End of Script!')
logger.debug('Runtime of script: {}'.format(end_time - start_time))
logger.debug("End of logging.\n\n")
