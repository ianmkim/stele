from gdelt import gdelt

if __name__ == "__main__":
    loader = gdelt.GDELT()
    loader.download()
    loader.archive_to_csv()
    loader.serialize_data()
    df = loader.load_serialized_data()