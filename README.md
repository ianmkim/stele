# Stele 
> A stele (/ˈstiːli/ STEE-lee), or occasionally stela (plural stelas or stelæ), when derived from Latin, is a stone or wooden slab. Stelae were occasionally erected as memorials to battles

Stele is a project investigating the the trend of geopolitical events through classical Machine Learning algorithms. The aim is three-fold:
 1. Distillation learning. Using the dataset already available, build better classifiers that work faster and with less input than the original models
 2. Predictive inference. Predict the course of future events.
 3. Bias investigation. Analyze the quality of sources to detect any aggregate or systematic bias against any given world power.
 
## Data Preparation
### GDELT
Supported by Google Jigsaw, the [GDELT Project](https://www.gdeltproject.org) automatically scrapes and monitors broadcast, print, and web news globally in over 100 languages and identifies organizations, people, and other metrics about world events. The database is updated daily with all the events that happened on that day, often exceeding tens of thousands of lines per day. 

We're particularly interested in the following metrics in order to deeply understand the trend of world events and gain predictive/fundamental understanding powers: `ActorCode` which specify what country is acting on what country, the `ActorType` which specifies the kind of organization, `EventCode` which specifies kinds of events, `QuadClass` which indicates rough levels of cooperation and violence, the `GoldsteinScale` which more measures levels of violence along different axes, `NumMentions` which quantify the number of times the event was mentioned in all sources, `AvgTone` which indicates average sentiment among all sources, the `SOURCEURL`, and finally, various geographic data.

### Memory Restraints & Parallel Processing
A large part of this project was figuring out how to deal with the exceptionally large corpus. First attempts to keep the dataset in-memory failed miserably as the system eventually ran out of memory and SWAP available.

We had to replace Pandas with Dask in order to explore the dataset in a fast, efficient, and high-throughput manner. Dask has a pandas and sklearn-like API and supports cross-compatibility for both libraries. However, it also provides functionality to break up dataframes into partitions and reads them from disk as needed. This retrieval can be performed in parallel. Additionally, computation can be performed all at once and only when its needed. Meaning I do not have to wait 2x the time if I wanted to load, then filter data. It would collapse the two tasks into one automatically, loading while filtering the data when `.compute()` is called.

All of the code related to GDELT data collection, cleaning, saving, and partitioning can be found in `stele/gdelt/gdelt.py`

## Data Analysis
### Distilation Learning
The methods present in `bin_classification.ipynb` and `classification.ipynb` try to predict known variables such as `AvgTone`, and `QuadClass` using less data than was necessary for the GDELT project to generate them in the first place. Roughly, we use a TF-IDF vectorizer alongside dimensionality reduction methods and classical ML classification methods to generate predictions simply based on the URL, instead of the whole news source.

#### Methods Used
Binary classification. Accuracy if randomly guessed: ~50%
| Method                     | f1-score |
|----------------------------|----------|
| Binary Logistic Regression | 0.805    |
| Linear SVM                 | 0.813    |
| Perceptron                 | 0.546    |

Multiclass Classification. Accuracy if randomly guessed: ~20%
| Method                  | f1-score |
|-------------------------|----------|
| Multiclass Perceptron   | 0.636    |
| Logistic Regression OvR | 0.565    |
| K Nearest Neighbors     | 0.666    |
| SVM                     | 0.679    |


### Predictive Inference
The methods present in `regression.ipynb` tries to predict the number of events occuring in any given day given the number of events for the last 29 days. Predicting the 'busy-ness' of arbitrary days given the last couple days

#### Methods Used
| Method                             | MSE   |
|------------------------------------|-------|
| Linear Regression                  | 0.065 |
| Linear Regression (Moving Average) | 0.019 |
| Ridge                              | 0.067 |
| Lasso                              | 0.896 |


### Bias Investigations
Methods present in the `clustering.ipynb` attempts to cluster events based on their journalistic reception (`AvgTone`), violence levels (`GoldsteinScale`), and destabilization level (`QuadClass`). Both DBSCAN and K-means clustering were used.

| Method  |
|---------|
| DBSCAN  |
| K-Means |


## Requirements
If you wish to start the data collection and preparation from scratch, a machine with at least 32GBs of RAM is recommended. If not, make sure to allocate a bunch of SWAP and expect to spend some time twiddling your thumbs. Because the dataset itself is quite large (27GBs uncompressed txt format), we used dask, a replacement for pandas that breaks down large dataframes into chunks and implements multi-core algorithms and lazy computation for faster compute. 

We save the data using a format called parquet, which is a de-facto industry standard for saving tabular data. With compression, the entire dataset shard amounts to around 5GBs on disk. If we wanted to, we could easily have filtered it down to a smaller chunk, but a large part of this project was also about discovering what kind of data from what time period would yield helpful and predictive results

Since some parts of the notebook require significant memory and compute power, I've listed the specifications of what this project was performed on:

| Component | Spec        |
|-----------|-------------|
| CPU       | i9-12900K   |
| GPU       | 2x RTX 3090 |
| VRAM      | 2x 24GB     |
| MEM       | 128GB       |
| SWAP      | 256GB       |


## Notes
 - Saving data to Parquet took around 10 minutes on a 24core CPU
 - memory usage never exceeded durin the preparation stage up to 32GBs