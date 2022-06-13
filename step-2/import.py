"""
Imports the complete Wiki dataset into Weaviate
"""

import json
import weaviate
from uuid import uuid3, NAMESPACE_DNS
from loguru import logger


def create_weaviate_schema(client):
    """
    ...
    """

    # flush the schema and data
    client.schema.delete_all()
    # create schema
    schema = {
        "classes": [
            {
                "class": "Article",
                "description": "A wikipedia article with a title and crefs",
                "vectorizer": "none",
                "vectorIndexConfig": {
                    "skip": True
                },
                "properties": [
                    {
                        "dataType": [
                            "string"
                        ],
                        "description": "Title of the article",
                        "name": "title",
                        "indexInverted": True
                    },
                    {
                        "dataType": [
                            "Paragraph"
                        ],
                        "description": "List of paragraphs this article has",
                        "name": "hasParagraphs",
                        "indexInverted": True
                    },
                    {
                        "dataType": [
                            "Article"
                        ],
                        "description": "Articles this page links to",
                        "name": "linksToArticles",
                        "indexInverted": True
                    }
                ]
            },
            {
                "class": "Paragraph",
                "description": "A wiki paragraph",
                "vectorIndexConfig": {
                    "vectorCacheMaxObjects": 150000000000,
                    "ef": 256,
                    "efConstruction": 512,
                    "maxConnections": 128
                },
                "properties": [
                    {
                        "dataType": [
                            "string"
                        ],
                        "description": "Title of the paragraph",
                        "name": "title",
                        "indexInverted": True,
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        }
                    },
                    {
                        "dataType": [
                            "text"
                        ],
                        "description": "The content of the paragraph",
                        "name": "content",
                        "indexInverted": True,
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        }
                    },
                    {
                        "dataType": [
                            "int"
                        ],
                        "description": "Order of the paragraph",
                        "name": "order",
                        "indexInverted": True,
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        }
                    },
                    {
                        "dataType": [
                            "Article"
                        ],
                        "description": "Article this paragraph is in",
                        "name": "inArticle",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        }
                    }
                ]
            }
        ]
    }
    #
    # add schema
    #
    client.schema.create(schema)


def add_article_to_batch(parsed_line):
    return [
        {
            "title": parsed_line["title"]
        },
        "Article",
        str(uuid3(NAMESPACE_DNS, parsed_line["title"].replace(" ", "_")))
    ]


def add_paragraph_to_batch(parsed_line):
    return_array = []
    for paragraph in parsed_line["paragraphs"]:
        add_object = {    
            "content": paragraph["content"],
            "order": paragraph["count"],
            "inArticle": [{
                "beacon": "weaviate://localhost/" + str(uuid3(NAMESPACE_DNS, parsed_line["title"].replace(" ", "_")))
            }]
        }
        if "title" in paragraph:
            # Skip if wiki paragraph
            if ":" in paragraph["title"]:
                continue
            add_object["title"] = paragraph["title"]
        # add to batch
        return_array.append([
            add_object,
            "Paragraph",
            str(uuid3(NAMESPACE_DNS, parsed_line["title"].replace(" ", "_") + str(paragraph["count"])))
        ])
    return return_array


def handle_results(results):
    if results is not None:
        for result in results:
            if 'result' in result and 'errors' in result['result'] and  'error' in result['result']['errors']:
                for message in result['result']['errors']['error']:
                    logger.debug(message['message'])


def import_data_without_crefs(wiki_data_file):
    counter = 1
    counter_article = 1
    with open(wiki_data_file) as f:
        for line in f:
            parsed_line = json.loads(line)
            if len(parsed_line["paragraphs"]) > 0:
                try:
                    article_obj = add_article_to_batch(parsed_line)
                    counter_article += 1
                    # skip if it is a standard wiki category
                    if ":" in article_obj[2]:
                        continue
                    else:
                        # add the article obj
                        client.data_object.create(article_obj[0], article_obj[1], article_obj[2])
                        counter += 1
                        # add the paragraphs
                        for item in add_paragraph_to_batch(parsed_line):
                            # add data object to batch
                            client.batch.add_data_object(item[0], item[1], item[2])
                            # add ref to batch
                            client.batch.add_reference(article_obj[2], "Article", "hasParagraphs", item[2])
                            logger.info("Imported (" + str(counter) + " / " + str(counter_article) + ") – " + parsed_line["title"] + " with # of paragraphs " + str(len(parsed_line["paragraphs"])))
                            counter += 1
                            if (counter % 500) == 0:
                                result = client.batch.create_objects()
                                result_refs = client.batch.create_references()
                                handle_results(result)
                except Exception as e:
                    counter += 1
                    logger.debug("Skipping: " + article_obj[2])
                    logger.debug(e)
                    pass
    client.batch.create_objects()


def import_data_crefs(wiki_data_file):
    counter = 1
    with open(wiki_data_file) as f:
        for line in f:
            parsed_line = json.loads(line)
            # skip if it is a standard wiki category
            if ":" in parsed_line["title"]:
                continue
            else:
                for cref in parsed_line["crefs"]:
                    article_uuid = str(uuid3(NAMESPACE_DNS, parsed_line["title"].replace(" ", "_")))
                    link_uuid = str(uuid3(NAMESPACE_DNS, cref))
                    with client.batch(batch_size=12000, dynamic=True) as batch:
                        results = client.batch.add_reference(article_uuid, "Article", "linksToArticles", link_uuid)
                        handle_results(results)
                    counter += 1
                logger.info("Crefs set (" + str(counter) + ") – " + parsed_line["title"])
            


if __name__ == "__main__":
    logger.info("Start import")
    # wiki data file
    wiki_data_file = "wikipedia-en-articles.json"
    # connect Weaviate
    client = weaviate.Client("http://localhost:8080")
    # create schema
    create_weaviate_schema(client)
    # import data objects without CREFs
    import_data_without_crefs(wiki_data_file)
    # import crefs
    import_data_crefs(wiki_data_file)
    # done
    logger.info("Done")
