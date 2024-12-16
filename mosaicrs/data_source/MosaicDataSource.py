from typing import Any
import requests
import json
import pandas as pd
import regex as re
import duckdb

from mosaicrs.data_source.DataSource import DataSource

#TODO: Überlegen, wie wir die Query zusammen mit den Argumenten übergeben, da die Query an sich auch ein Arguement ist an sich.


class MosaicDataSource(DataSource):
    SEARCH_PATH = "/search?"


    def __init__(self, url: str = "http://localhost:8008"):
        self.mosaic_url = url


    def request_data(self, query: str, arguments: dict[str, Any] = None, database_text_extraction: bool = False) -> pd.DataFrame:
        if re.search("^[a-zA-Z]+(\+[a-zA-Z]+)*$", query) is None:
            query = '+'.join(query.split(' '))
        
        if arguments is None:
            arguments = {}
        elif "q" in arguments and arguments["q"] != query:
            print("Error: Multiple different search terms found!")
            return None
        elif "q" not in arguments:
            arguments["q"] = query

        
        response = requests.get(''.join([self.mosaic_url, MosaicDataSource.SEARCH_PATH]), params=arguments)
        json_data = json.loads(response.text)

        docs = []

        for x in json_data['results']:
            for k, v in x.items():
                for d in v:
                    docs.append(d)

        df_docs = pd.DataFrame(docs)

        if not database_text_extraction:
            return df_docs


        #TODO: Abklären wie wir zu Infos kommen
        #Temporäre DB Anbindung

        ids = df_docs["id"].to_list()

        duckdb_file = "/tmp/mosaic_db"
        con = None

        try:
            con = duckdb.connect(duckdb_file, read_only = True)

        
            combined_search_ids = ", ".join(["'" + str(doc_id) + "'" for doc_id in ids])

            query = f"""SELECT * 
                        FROM owi_simplewiki
                        WHERE id IN ({combined_search_ids})"""
            df = con.execute(query).fetchdf()

            con.close()

            # for text in df["plain_text"].to_list():
            #     print(text + "\n\n")

            df_docs["textSnippet"] = df["plain_text"]

            return df_docs

        except Exception as e:
            print(f"An error occured:{e}")
        finally:
            if con is not None:
                con.close()