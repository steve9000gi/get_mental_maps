#!/usr/bin/env python

""" get_mental_maps.py: Retrieve and write as .json files all the system support
    maps (ssms) from the ssm database that are generated by the website
    http://syssci.renci.org/ssm-wizard-mental-health-in-schools/. Source for
    this website is available at
    https://github.com/steve9000gi/ssm/tree/wizard-mental-health-in-schools.

    Usage:
        get_mental_maps.py output_directory

    Arg:
        output_directory: a directory into which all the ssm .json files are to
        be written. If it doesn't exist it will be created.

    The "SELECT * from maps" statement returns a list of tuples. Each tuple is
    an ssm plus its associated metadata and is comprised of the following
    elements:

    index type      contents                 column name in database
    ___________________________________________________________________________
    0     int       map id                   id
    1     int       owner id                 owner
    2     dict      the ssm                  document 
    3     datetime  created timestamp        created_at
    4     datetime  last modified timestamp  modified_at
    5     str       map name                 name

    The tuples in the list are sorted in ascending order of the elements with 
    index 4 (last modified timestamp).

    The element at index 3 in each tuple in the list is a dict which contains
    the actual system support map. For the purposes of this study we're
    interested only in those dicts which contain a "schoolLocation" key
    because only those database elements are generated by the website custom-
    modified for the "Roles in Mental Health Care within Schools in Connecticut"
    research study.
    
    For each one of those ssms that meets this criterion, print some useful
    tracking info to stdout and write the dict to file in .json format.

    from PostGres database
    -> extract list of tuples
    -> examine each tuple of metadata + dict
    -> write dict with key "schoolLocation" to file
"""

import sys
import os
import psycopg2
import collections
import json
import string

def connect():
    """ Connect to ssm PostgreSQL database

        Args:
            None: hardwired to a particular database.

        Returns:
            connection to database.
     """
    conn = None
    try:
        print "Connecting to ssm database..."
        conn = psycopg2.connect(host = "",
                                database = "",
                                user = "")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return conn

def get_maps(sort_index):
    """ Get a list of tuples from the PostgreSQL database, each tuple of which
        is a dict representing an ssm plus associated metadata.

        Arg: 
            sort_index: the int index of the tuple elements to be used as the
            basis for sorting the tuples in the list.

        Returns:
            a sorted list of tuples.
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * from maps")
    maps = cur.fetchall()
    cur.close()
    conn.close()
    print "number of maps fetched: " + str(len(maps))
    return sorted(maps, key=lambda k: k[sort_index])

def print_header():
    print ("     Location of school                  Size (bytes)     " +
    "Last modified")
    print "_" * 74
 
def get_pad1(n):
    """ Whitespace padding for right-aligning printed integers.

        Arg:
            n: the integer to be right-aligned. Assumes that n < 10000.

       Returns:
            a string with the appropriate amount of whitespace.
    """
    if n < 10:
        return "   "
    if n < 100:
        return "  "
    if n < 1000:
        return " "
    return ""

def get_pad2(s1, s2):
    """ Returns a string of whitespace padding to insert between strings s1
        and s2 so that the length of s1 + padding + s2 = 40.
    """
    return " " * (40 - len(s1) - len(s2))

def print_row(n, loc, sz, last_modified):
    """ Print some handy tracking info about an ssm to stdout.

        Args:
            n: integer row number.
	    loc: string place location (assumed to be from the current ssm).
            sz: integer size in bytes of the current ssm as a string.
            last_modified: string represenatation of datetime object.

        Returns:
            Nothing
    """
    print (get_pad1(n) + str(n) + ". " + loc  + get_pad2(loc, sz) +
    sz + " " * 13 + last_modified)

def build_output_file_path(dir, loc, id):
    """ Create a full path for an ssm file.

        Args:
            dir: string path to directory, either relative or absolute. No 
            checking to see if the path is valid.
            loc: string place name to be used in assembling the file name.
            id: integer to be used in assembling the file name.

        Returns:
            cleaned-up string (spurious whitespace and punctuation removed) to
            be used as full path to .json file.
    """
    clean_dir = dir.rstrip("/")
    clean_loc = loc.strip().translate(None, string.punctuation)
    clean_loc = clean_loc.replace(" ", "_")
    return clean_dir + "/ssm-" + clean_loc + "-" + str(id) + ".json"

def write_map_to_file(dir, loc, map_id, d):
    """ Write a dict to an ssm .json file.

        Args:
            dir: string path to directory.
            loc: string place name used to build file name.
            map_id: int used to build file name.
            d: the dict that's to be written to file as .json.

        Returns:
            Nothing
    """
    if not os.path.exists(dir):
        os.makedirs(dir)
    path =  build_output_file_path(dir, loc, map_id)
    with open(path, "w") as f:
        json.dump(d, f, sort_keys=True, indent=4)
        f.close()

def main():
    IX_SSM_ID = 0
    IX_OWNER_ID = 1
    IX_DOC = 2
    IX_MODIFIED_AT = 4
    IX_SSM_NAME = 5
    dir = sys.argv[1]
    maps = get_maps(IX_MODIFIED_AT)
    n = 0
    print_header()
    for map in maps:
        map_id = map[IX_SSM_ID]
        owner = map[IX_OWNER_ID]
        last_modified = map[IX_MODIFIED_AT].strftime("%Y-%m-%d %H:%M")
        name = map[IX_SSM_NAME]
        d = map[IX_DOC]
        if "schoolLocation" in d and owner not in [2, 20]: # exclude SC, KHL
            n += 1
            sz = str(len(str(d)))
            loc = str(d["schoolLocation"])
            print_row(n, loc, sz, last_modified)
            write_map_to_file(dir, loc, map_id, d)

if __name__ == "__main__":
    main()
