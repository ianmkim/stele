import sys 
sys.path.append("..")

from constants import major_actors

import requests
import lxml.html as lh

import time
import os.path
import urllib
import zipfile
import glob
import operator

import glob
import pandas as pd
from pprint import pprint

from tqdm import tqdm

from urllib.request import urlretrieve

from typing import List

class GDELT(): 
    def __init__(self, data_path:str="./data/",
                        verbose:bool=True,
                        fips_country_code:str=""):
        self.gdelt_base_url = "http://data.gdeltproject.org/events/"
        self.data_path = data_path
        self.verbose = verbose
        self.file_list = self.get_file_list()
        self.fips_country_code = fips_country_code
        self.tqdm_c = tqdm if self.verbose else list

    def get_file_list(self) -> List[str]:
        page = requests.get(self.gdelt_base_url + "index.html")
        doc = lh.fromstring(page.content)
        link_list = doc.xpath("//*/ul/li/a/@href")
        file_list = [x for x in link_list if str.isdigit(x[0:4])]
        return file_list

    def download(self, limit:int=1000, 
                        download_delay:float=0.1):
        infilecounter = 0
        for compressed_file in self.tqdm_c(self.file_list[infilecounter:limit]):
            while not os.path.isfile(self.data_path + compressed_file): 
                time.sleep(download_delay)
                try:
                    urlretrieve(url=self.gdelt_base_url + compressed_file,
                                filename=self.data_path + compressed_file)
                except Exception as ex:
                    print(ex)
                    print(f"Could not download file {self.gdelt_base_url + compressed_file}")
                    break

    def archive_to_csv(self, limit:int=1000, remove_after_conversion:bool=True):
        infilecounter = 0
        outfilecounter = 0
        skipped_files = 0
        for compressed_file in self.tqdm_c(self.file_list[infilecounter:limit]):
            if os.path.isfile(self.data_path + compressed_file):
                if os.path.isfile(self.data_path + "country/" + self.fips_country_code + "_%04i.tsv"%outfilecounter):
                    skipped_files += 1
                    continue
                z = zipfile.ZipFile(file=self.data_path + compressed_file, mode="r")
                z.extractall(path=self.data_path + "tmp/")
                
                for infile_name in glob.glob(self.data_path + "tmp/*"):

                    self._archive_to_csv(infile_name, outfilecounter)
                    outfilecounter += 1
                    if remove_after_conversion:
                        os.remove(infile_name)

                infilecounter += 1
        if(infilecounter == 0 and skipped_files == 0):
            print("No files were converted, please call download() before converting to csv")


    def _archive_to_csv(self, infile_name:str, outfilecounter:int):
        outfile_name = self.data_path + "country/" + self.fips_country_code + "_%04i.tsv"%outfilecounter
        with open(infile_name, "r") as infile, open(outfile_name, "w") as outfile:
            for line in infile:
                try:
                    country_set = operator.itemgetter(51, 37, 44)(line.split("\t"))
                except:
                    print("couldn't find row's fips")
                    country_set = ()
                
                # only save the actions done by major countries. You can see the full list
                # of what countries are considered "major" in the MAJOR_ACTORS_FIPS object
                # in the constants.py file.
                in_major_fips = False
                for country in country_set:
                    in_major_fips = country in major_actors.MAJOR_ACTORS_FIPS


                if in_major_fips:
                    outfile.write(line)


    def serialize_data(self, outfile_name:str="gdelt.hdf"):
        colnames = pd.read_excel("gdelt_headers.xlsx", 
                                sheet_name="Sheet1",
                                index_col="Column ID")["Field Name"]
        if os.path.isfile(self.data_path + outfile_name):
            return
        files = glob.glob(self.data_path + "country/" + self.fips_country_code + "*")
        list_dfs = []
        for active_file in self.tqdm_c(files): 
            record = pd.read_csv(active_file, 
                        sep="\t", 
                        header=None, 
                        dtype=str, 
                        names=colnames, 
                        index_col=["GLOBALEVENTID"])
            list_dfs.append(record)

        print("starting concatenation")
        final_df = pd.concat(list_dfs).astype(str, copy=False)
        print("finished concatenation")
        final_df.to_hdf(self.data_path + outfile_name,
                        "dat",
                        complevel=0,
                        complib="zlib")
        """
        with open(self.data_path + outfile_name, "wb") as file:
            msgpack.pack(df_list, file, use_bin_type=True)
        """