#!/usr/bin/python
#
# Author    Yann Bayle
# E-mail    bayle.yann@live.fr
# License   MIT
# Created   13/10/2016
# Updated   18/10/2016
# Version   1.0.0
#

"""
Description of kea.py
======================

Reproduce:
source activate py27
cd /media/sf_DATA/Code/Gouyon/packageRepro/package/TableII/MARSYAS_CAL97/
python run_autotagging_framework.py /media/sf_DATA/Code/Gouyon/packageRepro/package/TableII/MARSYAS_CAL97/

Info:
https://github.com/marsyas/marsyas/blob/master/src/apps/kea/kea.cpp

:Example:

python kea.py
./clean.sh ; python kea.py -n 5 -i /media/sf_DATA/Datasets/Simbals/marsyas/results/ -g /media/sf_DATA/Datasets/Simbals/groundtruth.csv

.. todo::
Generate train/test de kea
Lancer kea sur train/test
replace shutil by os or sys

"""

import os
import csv
import sys
import time
import utils
import shutil
import argparse
import multiprocessing
from scipy.io import arff

begin = int(round(time.time() * 1000))

def validate_arff(filename):
    """Description of validate_arff

    Check if filename exists on path and is a file
    If file corresponds to valid arff file return absolute path
    Otherwise move file to invalid directory and return False
    """
    # Check if file exists
    if os.path.isfile(filename) and os.path.exists(filename):
        filename = os.path.abspath(filename)
    else:
        return False
    # If does not satisfy min size, move to "empty" folder
    if os.stat(filename).st_size < 8100:
        tmp_path = filename.split("/")
        empty_dirname = "/".join(tmp_path[:-1]) + "/empty/"
        if not os.path.exists(empty_dirname):
            os.makedirs(empty_dirname)
        shutil.move(filename, empty_dirname + tmp_path[-1])
        return False
    # If filename does not match with feature name, move to "invalid" folder
    name_file = filename.split("/")[-1][:12]
    with open(filename) as filep:
        for i, line in enumerate(filep):
            if i == 70:
                # 71th line
                name_feat = line.split(" ")[2][1:13]
                break
    if name_file != name_feat:
        tmp_path = filename.split("/")
        invalid_dirname = "/".join(tmp_path[:-1]) + "/invalid/"
        if not os.path.exists(invalid_dirname):
            os.makedirs(invalid_dirname)
        shutil.move(filename, invalid_dirname + tmp_path[-1])
        return False
    # If everything went well, return filename absolute path
    return filename

def merge_arff(indir, outfilename):
    """Description of merge_arff

    bextract programm from Marsyas generate one output file per audio file
    This function merge them all in one unique file
    Check if analysed file are valid i.e. not empty
    """
    utils.print_success("Preprocessing ARFFs")
    indir = utils.abs_path_dir(indir)
    tmpfilename = "tmp_arff.txt"
    os.system("ls " + indir + " > " + tmpfilename)
    with open(tmpfilename, 'r') as filenames:
        outfn = open(outfilename, 'w')
        cpt_invalid_fn = 0
        # Write first lines of ARFF template file
        for filename in filenames:
            filename = validate_arff(indir + "/" + filename[:-1])
            if filename:
                with open(filename, 'r') as template:
                    nb_line = 77
                    for line in template:
                        if not nb_line:
                            break
                        nb_line -= 1
                        outfn.write(line)
                    break
            else:
                cpt_invalid_fn += 1
        # Append all arff file to the output file
        cur_file_num = 1
        for filename in filenames:
            filename = validate_arff(indir + "/" + filename[:-1])
            if filename:
                cur_file_num = cur_file_num + 1
                sys.stdout.write("\r\tAnalysing file\t" + str(cur_file_num))
                sys.stdout.flush()
                fname = open(filename,'r')
                outfn.write("".join(fname.readlines()[74:77]))
                fname.close()
            else:
                cpt_invalid_fn += 1
        sys.stdout.write('\n')
        sys.stdout.flush()
        outfn.close()
    os.remove(tmpfilename)
    if cpt_invalid_fn:
        utils.print_warning(str(cpt_invalid_fn) + " ARFF with errors found")
    utils.print_success("Preprocessing done")
    return outfilename

def add_groundtruth(feature_fn, groundtruth_fn, output_fn):
    """Description of add_groundtruth

    Write in output filename the groundtruth merged with corresponding features

    ..todo:: Error with old_tag not corresponding to filename...


    """
    utils.print_success("Adding groundtruth")
    feature_fn = utils.abs_path_file(feature_fn)
    groundtruth_fn = utils.abs_path_file(groundtruth_fn)
    if os.path.isfile(output_fn) and os.path.exists(output_fn):
        utils.print_warning("Overwritting existing output file: " + 
            utils.abs_path_file(output_fn))
    # TODO Read groundtruth file in memory
    tmp_gt = csv.reader(open(groundtruth_fn, "r"))
    groundtruths = {}
    for row in tmp_gt:
        groundtruths[row[0]] = row[1]
    tags = []
    output = open(output_fn, "w")
    with open(feature_fn, "r") as feat:
        line_num = 0
        tmp_line = ""
        for line in feat:
            line_num += 1
            if line_num > 74:
                if line[0] != "%":
                    # Alter feature line with correct tag
                    cur_line = line.split(",")
                    old_tag = cur_line[-1].split("_")[0]
                    if old_tag in groundtruths:
                        new_tag = groundtruths[old_tag]
                        output.write(tmp_line + ",".join(cur_line[:-1]) + "," + new_tag +"\n")
                        tmp_line = ""
                        tags.append(new_tag)
                    else:
                        # TODO
                        # File not in groundtruth
                        tmp_line = ""
                        # utils.print_warning("Error with " + old_tag)
                else:
                    tmp_line += line
            elif line_num == 2:
                output.write("@relation train_test.arff\n")
                # output.write("@relation MARSYAS_KEA\n")
            elif line_num == 71:
                # Alter line 71 containing all tag gathered along the way
                # TODO enhance
                output.write("@attribute output {i,s}\n")
            else:
                # Write header
                output.write(line)
    
    tags = list(set(tags))
    utils.print_warning("TODO Take in account diffents tags than " + str(tags))
    
    output.close()
    utils.print_success("Groundtruth added")

def split_number(number, nb_folds):
    """Description of split_number

    Return an int array of size nb_folds where the sum of cells = number
    All the integers in cells are the same +-1 
    """
    if not isinstance(number, int) and not isinstance(nb_folds, int):
        utils.print_error("Variable must be integer")
    if number < nb_folds:
        utils.print_error("Number of folds > Number of data available")
    min_num = int(number/nb_folds)
    folds = [min_num] * nb_folds
    for num in range(0, number-(min_num*nb_folds)):
        folds[num] = folds[num] + 1
    return folds

def create_folds(filelist, nb_folds, invert_train_test=False):
    """Description of create_folds

    """
    utils.print_success("Creating folds")
    if nb_folds < 1:
        utils.print_error("Wrong number of folds provided")

    folds_dir = "/".join(filelist.split("/")[:-1])
    if nb_folds == 1:
        # Train and test set are the same
        folds_dir = folds_dir + "/01_fold"
        utils.create_dir(folds_dir)
        os.system("cp " + filelist + " " + folds_dir + "/train_test.arff")
    else:
        # Create train and test set
        folds_dir = folds_dir + "/" + str(nb_folds).zfill(2) + "_folds"
        utils.create_dir(folds_dir)
        # TODO
        # Read filelist
        # Extract name and tag
        # Separate different tag
        # create folds
        data, meta = arff.loadarff(filelist)
        tags = {}
        for row in data:
            tag = row[-1].decode("ascii")
            if tag in tags:
                tags[tag] += 1
            else:
                tags[tag] = 1
        tags_folds = {}
        tags_folds_index = {}
        for tag in tags:
            tags_folds[tag] = split_number(tags[tag], nb_folds)
            tags_folds_index[tag] = 0
        # Create empty folds
        folds = {}
        # Init empty folds
        for index in range(0, nb_folds):
            folds[index] = ""
        # Fill folds with data
        with open(filelist, "r") as filelist_pointer:
            arff_header = ""
            tmp = ""
            for i, line in enumerate(filelist_pointer):
                sys.stdout.write("\r\t" + str(i))
                sys.stdout.flush()
                # Until the 75th line
                if i > 74:
                    # Process ARFF data
                    if "% " in line:
                        # Memorize line
                        tmp += line
                    else:
                        # Get line 3 and add it to corresponding fold
                        tag = line.split(",")[-1][:-1]
                        num_fold = tags_folds_index[tag]
                        if tags_folds[tag][num_fold] == 0:
                            tags_folds_index[tag] += 1
                        tags_folds[tag][tags_folds_index[tag]] -= 1
                        folds[tags_folds_index[tag]] += tmp + line
                        tmp = ""
                else:
                    # Save ARFF header lines
                    arff_header += line
            sys.stdout.write('\n')
            sys.stdout.flush()
        # At this point data has been split up in different part
        # Use this part to create train/test split
        if invert_train_test:
            # Test is bigger than train
            fn_with_min_data = "/train_"
            fn_with_max_data = "/test_"
        else:
            # Train is bigger than test
            fn_with_min_data = "/test_"
            fn_with_max_data = "/train_"
        for index_test in range(0, nb_folds):
            filep = open(folds_dir + fn_with_min_data + str(index_test+1).zfill(2) + ".arff", "a")
            filep.write(arff_header + folds[index_test])
            filep.close()
            filep = open(folds_dir + fn_with_max_data + str(index_test+1).zfill(2) + ".arff", "a")
            for index_train in range(0, nb_folds):
                if index_train != index_test:
                    filep.write(arff_header + folds[index_train])
            filep.close()
        utils.print_success("Done")
    return folds_dir

def run_kea(train_file, test_file, out_file):
    """Description of run_kea

    Launch kea classification on specified file
    """
    kea_cmd = 'kea -m tags -w ' + train_file + ' -tw ' + test_file + ' -pr ' + out_file
    os.system(kea_cmd)

def run_kea_on_folds(folds_dir):
    """Description of run_kea_on_folds

    Wrapper for kea on folds
    """
    folds_dir = utils.abs_path_dir(folds_dir)
    out_file = folds_dir + "/results.txt"
    if os.path.exists(folds_dir + "/train_test.arff"):
        train_file = folds_dir + "/train_test.arff"
        test_file = train_file
        run_kea(train_file, test_file, out_file)
    else:
        nb_folds = len([name for name in os.listdir(folds_dir) if os.path.isfile(os.path.join(folds_dir, name))])
        # Run on multiple train/test
        for index in range(1, int(nb_folds/2)+1):
            utils.print_success("Train/Test on fold " + str(index))
            train_file = folds_dir + "/train_" + str(index).zfill(2) + ".arff"
            test_file = folds_dir + "/test_" + str(index).zfill(2) + ".arff"
            out_file = folds_dir + "/results_" + str(index).zfill(2) + ".arff"
            run_kea(train_file, test_file, out_file)

        utils.print_warning("TODO multiprocessing")
        # # Parallel computing on each TrainTestFolds
        # printTitle("Parallel train & test of folds")
        # partialRunTrainTestOnFold = partial(runTrainTestOnFold, args=args)
        # pool = multiprocessing.Pool()
        # pool.map(partialRunTrainTestOnFold, range(nb_folds)) #make our results with a map call
        # pool.close() #we are not adding any more processes
        # pool.join() #tell it to wait until all threads are done before going on

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Validate list of ISRCs")
    PARSER.add_argument(
        "-i",
        "--input_dir",
        help="input directory containing all ARFF file from Marsyas bextract",
        type=str,
        default="data",
        metavar="input_dir")
    PARSER.add_argument(
        "-o",
        "--output_file",
        help="output file",
        type=str,
        default="feat_with_groundtruth.txt",
        metavar="output_file")
    PARSER.add_argument(
        "-g",
        "--groundtruth_file",
        help="groundtruth file",
        type=str,
        default="groundtruth.txt",
        metavar="groundtruth_file")
    PARSER.add_argument(
        "-n",
        "--nb_folds",
        default=1,
        type=int,
        metavar="nb_folds",
        help="classification folds number, must be >= 1, default = 1")

    utils.print_success("Kea classification")
    # Variable declaration
    input_dir = PARSER.parse_args().input_dir
    res_dir = "analysis"
    utils.create_dir(res_dir)
    if input_dir[-1] == "/":
        input_dir = input_dir[:-1]
    proj_dir = res_dir + "/" + input_dir.split("/")[-1]
    utils.create_dir(proj_dir)
    feat_without_groundtruth = proj_dir + "/feat_without_groundtruth.arff"
    feat_with_groundtruth = proj_dir + "/" + PARSER.parse_args().output_file
    # Functions call
    merge_arff(input_dir, feat_without_groundtruth)
    add_groundtruth(feat_without_groundtruth,
        PARSER.parse_args().groundtruth_file,
        feat_with_groundtruth)
    os.remove(feat_without_groundtruth)
    folds_dir = create_folds(feat_with_groundtruth, PARSER.parse_args().nb_folds, invert_train_test=True)
    run_kea_on_folds(folds_dir)

# 2 merge all arff files dans train/test file (generate train/test folds/set,
#   reuse vqmm) à partir des fichiers sources d'un autre dossier, tout copier
#   dans dossier de svmbff. no-overlap train/Test
# 3 lancer kea sur toutes les train/test
# 4 Afficher les résultats

    utils.print_success("Finished in " + str(int(round(time.time() * 1000)) - begin) + "ms")
