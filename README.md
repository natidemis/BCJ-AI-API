# Artificial intelligence API for BCJ
Artificial Intelligence API for usability problems.

***

# Todo

- Útskýra að við notum google_news og endurnefndum skjalið í google_news.bin

***

## Authors

- Kristófer Ásgeirsson - ``kra33``
- Marcelo Felix Audibert - `Gitcelo`
- Natanel Demissew Ketema - `natidemis`

***

## Dependencies

*All dependencies can be found in the file `requirements.txt`.*

***

## Setup

- Install dependencies by writing ``pip install -r requirements.txt`` into terminal
    * Note that the versions in the file may be outdated
    
- Run ``gentoken.py`` to generate a secret token
    * The token appears in a new file called ``config.py``
    * The token has to be in header as bearer token when making HTTP requests to the server

***

## Run

Run the file run.py to start the server (e.g. by writing ``python run.py`` in terminal).

The pacakge NLTK should install itself with stopwords if it isn't already installed. If it doesn't install itself, write the following into a python console:

```
>>> import nltk
>>> nltk.download('stopwords')
```
***

## Example of HTTP request to server made in Python

```python
import requests

url = "<your-url>/bug"
token = "my bearer token"
json = {
    "summary": "summ",
    "description": "desc",
    "structured_info": {
        "id": 1,
        "bucket": "somrh",
        "date": "2015-02-28"
    }
}

response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(token)},json = json)
```

***

## Web service
* `/bug`
  * `GET` query the **k** most similar bugs
  * `POST` insert a bug 
    * data requirement for request: summary and description must be string values, may be empty strings. id must be a number or a number in string format, creationDate must be a string in the following format: YYY-MM-DD. Structured_info must be valid for insertion. `{
   "summary": "summary",
   "description": "description,
   "structured_info": {id, creationDate}
 }` 
  * `DELETE` delete a bug 
     * valid id in the format: `{ "id": "id" }`
  * `PATCH` update a bug 
* `/batch`
  * `POST` insert k bugs 
  * `DELETE` delete k bugs 
  
***

