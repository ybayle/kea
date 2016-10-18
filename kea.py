#!/usr/bin/python
#
# Author    Yann Bayle
# E-mail    bayle.yann@live.fr
# License   MIT
# Created   13/10/2016
# Updated   17/10/2016
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

.. todo:: 
Merge groundtruth avec arff de kea.py
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

begin = int(round(time.time() * 1000))

def validate_arff(filename):
    """Description of validate_arff

    Check if filename exists on path and is a file
    If file corresponds to valid arff file return absolute path
    Otherwise move file to invalid directory and return False
    """
    filename = utils.abs_path_file(filename)
    if os.stat(filename).st_size < 8100:
        tmp_path = filename.split("/")
        invalid_dirname = "/".join(tmp_path[:-1]) + "/invalid/"
        if not os.path.exists(invalid_dirname):
            os.makedirs(invalid_dirname)
        shutil.move(filename, invalid_dirname + tmp_path[-1])
        return False
    else:
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
        cpt_invalid_filename = 0
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
                cpt_invalid_filename += 1
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
                cpt_invalid_filename += 1
        sys.stdout.write('\n')
        sys.stdout.flush()
        outfn.close()
    os.remove(tmpfilename)
    if cpt_invalid_filename:
        utils.print_warning(str(cpt_invalid_filename) + " invalid ARFF found")
    utils.print_success("Preprocessing done")
    return outfilename

def split_number(number, nb_folds):
    """Description of split_number

    Return an int array of size nb_folds where the sum of cells = number
    All the integers in cells are the same +-1 
    """
    if not isinstance(number, int) and not isinstance(nb_folds, int):
        printError("Variable must be integer")
    if number < nb_folds:
        printError("Number of folds > Number of data available")
    min_num = int(number/nb_folds)
    folds = [min_num] * nb_folds
    for num in range(0, number-(min_num*nb_folds)):
        folds[num] = folds[num] + 1
    return folds

def add_groundtruth(feature_fn, groundtruth_fn, output_fn):
    """Description of add_groundtruth

    Write in output filename the groundtruth merged with corresponding features

    ..todo:: Error with old_tag not corresponding to filename...

    """
    utils.print_success("Adding groundtruth")
    feature_fn = utils.abs_path_file(feature_fn)
    groundtruth_fn = utils.abs_path_file(groundtruth_fn)
    if os.path.isfile(output_fn) and os.path.exists(output_fn):
        utils.print_warning("Overwritting existing output file: " + output_fn)
    # TODO Read groundtruth file in memory
    tmp_gt = csv.reader(open(groundtruth_fn, "r"))
    groundtruths = {}
    for row in tmp_gt:
        groundtruths[row[0]] = row[1]
    tags = []
    output = open(output_fn, "w")
    with open(feature_fn, "r") as feat:
        line_num = 0
        for line in feat:
            line_num += 1
            if line_num > 74 and line[0] != "%":
                # Alter feature line with correct tag
                cur_line = line.split(",")
                old_tag = cur_line[-1].split("_")[0]
                if old_tag in groundtruths:
                    new_tag = groundtruths[old_tag]
                    output.write(",".join(cur_line[:-1]) + "," + new_tag +"\n")
                    tags.append(new_tag)
                else:
                    utils.print_warning("Error with " + old_tag)
            elif line_num == 71:
                # Alter line 71 containing all tag gathered along the way
                # TODO enhance
                output.write("@attribute output {i,s}")
            else:
                # Copy normal lines
                output.write(line)
    
    tags = list(set(tags))
    utils.print_warning("TODO Take in account diffents tags than " + str(tags))
    
    output.close()
    utils.print_success("Groundtruth added")

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
        default="arff/feat_with_groundtruth.txt",
        metavar="output_file")
    PARSER.add_argument(
        "-g",
        "--groundtruth_file",
        help="groundtruth file",
        type=str,
        default="groundtruth.txt",
        metavar="groundtruth_file")

    utils.print_success("Kea classification")
    tmpfilename = "arff/feat_without_groundtruth.arff"
    merge_arff(PARSER.parse_args().input_dir, tmpfilename)
    add_groundtruth(tmpfilename, PARSER.parse_args().groundtruth_file, PARSER.parse_args().output_file)

# 2 merge all arff files dans train/test file (generate train/test folds/set,
#   reuse vqmm) à partir des fichiers sources d'un autre dossier, tout copier
#   dans dossier de svmbff. no-overlap train/Test
# 3 lancer kea sur toutes les train/test
# 4 Afficher les résultats

    # train_file = "arff/train_file.arff"
    # test_file = "arff/test_file.arff"
    # output_file = "res/output_file.txt"

    # kea_cmd = 'kea -m tags -w ' + train_file + ' -tw ' + test_file + ' -pr ' + output_file
    # print(kea_cmd)
    # os.system(kea_cmd)

    utils.print_success("Finished in " + str(int(round(time.time() * 1000)) - begin) + "ms")
