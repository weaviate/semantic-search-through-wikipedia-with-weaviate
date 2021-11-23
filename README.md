# Semantic search through Wikipedia with the Weaviate vector search engine

[Weaviate](https://www.semi.technology/developers/weaviate/current/) is an open source vector search engine with build-in vectorization and question answering modules. We imported the complete English language Wikipedia article dataset into a single Weaviate instance to conduct semantic search queries through the Wikipedia articles, besides this, we've made all the graph relations between the articles too. We have made the import scripts, pre-processed articles, and backup available so that you can run the complete setup yourself. 

In this repository, you'll find the 3-steps needed to replicate the import, but there are also downlaods available to skip the first two steps.

If you like what you see, a ⭐ on the [Weaviate Github repo](https://github.com/semi-technologies/weaviate/stargazers) is appreciated.

Additional links:

* [Weaviate documentation](https://www.semi.technology/developers/weaviate/current/)
* [Weaviate on Github](https://github.com/semi-technologies/weaviate)
* [PyTorch-BigGraph search with the Weaviate vector search engine (similar project)](https://github.com/semi-technologies/PyTorch-BigGraph-search-with-Weaviate)

### Acknowledgments

* The [`t2v-transformers` module](https://www.semi.technology/developers/weaviate/current/modules/text2vec-transformers.html) used contains the [multi-qa-MiniLM-L6-cos-v1]() transformer created by the [SBERT team](https://www.sbert.net/)
* Thanks to the team of [Obsei](https://github.com/obsei/obsei) for sharing the idea on our [Slack](https://join.slack.com/t/weaviate/shared_invite/zt-goaoifjr-o8FuVz9b1HLzhlUfyfddhw) channel

### Stats

| description | value |
| --- | --- |
| Articles imported | `11.348.257` |
| Paragaphs imported | `27.377.159` | 
| Graph cross references | `125.447.595` |
| Wikipedia version | `truthy October 9th, 2021` | 
| Machine for inference | `12 CPU – 100 GB RAM – 200Gb SSD` |  
| Weaviate version | `v1.7.2` |
| Dataset size | `122GB` |

## Import

There are 3-steps in the import process. **You can also skip the first two and [directly import the backup](#step-3-query-the-dataset)**

### Step 1: Process the Wikipedia dump

In this process, the Wikipedia dataset is processed and cleaned (the markup is removed, HTML tags are removed, etc). The output file is a [JSON Lines](https://jsonlines.org/) document that will be used in the next step.

Process from the Wikimedia dump:

```sh
$ cd step-1
$ wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
$ bzip2 -d filename.bz2
$ pip3 install -r requirements.txt
$ python3 process.py
```

The import takes a few hours, so probably you want to do something like:

```sh
$ nohup python3 -u process.py &
```

You can also download the processed file from October 9th, 2021, and skip the above steps

```sh
$ wget https://storage.googleapis.com/semi-technologies-public-data/wikipedia-en-articles.json.gz
$ gunzip wikipedia-en-articles.json.gz
```

### Step 2: Import the dataset and vectorized the content

Weaviate takes care of the complete import and vectorization process but you'll need some GPU and CPU muscle to achieve this. Important to bear in mind is that this is _only_ needed on import time. If you don't want to spend the resources on doing the import, you can go to the next step in the process and download the Weaviate backup. The machine needed for inference is way cheaper.

We will be using a single Weaviate instance, but four Tesla T4 GPUs that we will stuff with 8 models each. To efficiently do this, we are going to add an NGINX load balancer between Weaviate and the vectorizers.

![Weaviate Wikipedia import architecture with transformers and vectorizers](https://semi.technology/img/4GPU-wikipedia-dataset.png "Weaviate Wikipedia import architecture with transformers and vectorizers")

* Every Weaviate [text2vec-module](https://www.semi.technology/developers/weaviate/current/modules/text2vec-transformers.html) will be using a [multi-qa-MiniLM-L6-cos-v1](https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1) sentence transformer.
* The volume is mounted _outside_ the container to `/var/weaviate`. This allows us to use this folder as a backup that can be imported in the next step.
* Make sure to have Docker-compose _with_ GPU support [installed](https://gist.github.com/bobvanluijt/af6fe0fa392ca8f93e1fdc96fc1c86d8).
* The import scripts assumes that the JSON file is called `wikipedia-en-articles.json`.

```sh
$ docker-compose up -d
$ import.py
```

The import takes a few hours, so probably you want to do something like:

```sh
$ nohup python3 -u import.py &
```

After the import is done, you can shut down the Docker containers by running `docker-compose down`.

### Step 3: Query the dataset!

{% note %}

**Note:** Start here if you want to work with a backup of the dataset without importing it

{% endnote %}

You can now run the dataset! We would advise running it with 1 GPU, but you can also run it on CPU only (without Q&A). The machine you need for inference is significantly smaller.

Note that Weaviate needs some time to import the backup (if you use the setup mentioned above +/- 15min). You can see the status of the backup in the docker logs of the Weaviate container.

```sh
# clone this repository
$ git clone https://github.com/semi-technologies/semantic-search-through-Wikipedia-with-Weaviate/
# go into the backup dir
$ cd step-3
# download the Weaviate backup
$ curl https://storage.googleapis.com/semi-technologies-public-data/weaviate-1.8.0-rc.2-backup-wikipedia-py-en-multi-qa-MiniLM-L6-cos.tar.gz -O
# untar the backup (112G unpacked)
$ tar -xvzf weaviate-1.8.0-rc.2-backup-wikipedia-py-en-multi-qa-MiniLM-L6-cos.tar.gz
# get the unpacked directory
$ echo $(pwd)/var/weaviate
# use the above result (e.g., /home/foobar/weaviate-disk/var/weaviate)
#   update volumes in docker-compose.yml (NOT PERSISTENCE_DATA_PATH!) to the above output
#   (e.g., PERSISTENCE_DATA_PATH: '/home/foobar/weaviate-disk/var/weaviate:/var/lib/weaviate')
#   With 16 CPUs this process takes about 12 to 15 minutes
```

#### With GPU

```sh
$ cd step-3
$ docker-compose -f docker-compose-gpu.yml up -d
```

#### Without GPU

```sh
$ cd step-3
$ docker-compose -f docker-compose-no-gpu.yml up -d
```

## Example queries

...

## Video

[VIDEO]
