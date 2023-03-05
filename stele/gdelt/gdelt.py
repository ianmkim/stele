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
import dask.dataframe as dd
from dask.diagnostics import ProgressBar
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

    def load_serialized_data(self, path:str="output"):
        if not os.path.isfile(self.data_path + path + "/part.0.parquet"):
            print("No serialized data found")
        return dd.read_parquet(self.data_path + path)

    def serialize_data(self):
        colnames = pd.read_excel("gdelt_headers.xlsx", 
                                sheet_name="Sheet1",
                                index_col="Column ID")["Field Name"]
        if os.path.isfile(self.data_path + "output/part.0.parquet"):
            return
        files = glob.glob(self.data_path + "country/" + self.fips_country_code + "*")
        final_df = None
        list_dfs = []
        for idx, active_file in enumerate(self.tqdm_c(files)):
            record = dd.read_csv(active_file, 
                        sep="\t", 
                        header=None, 
                        dtype=str, 
                        names=colnames).set_index("GLOBALEVENTID")
            list_dfs.append(record)
            if idx % 300== 0:
                if final_df is None:
                    final_df = dd.multi.concat(list_dfs)
                else:
                    concatted = dd.multi.concat(list_dfs)
                    final_df = dd.multi.concat([final_df, concatted])
                list_dfs = []

        concatted = dd.concat(list_dfs)
        final_df = dd.concat([final_df, concatted])
        del concatted
        del list_dfs

        # threads - requires little memory < 16GB
        # process - requires at least 64GB with 24 cores.
        with ProgressBar():
            final_df.to_parquet("data/output")

        """
        with open(self.data_path + outfile_name, "wb") as file:
            msgpack.pack(df_list, file, use_bin_type=True)
        """