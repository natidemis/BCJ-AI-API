# Artificial intelligence API for BCJ
Artificial Intelligence API for usability problems.

***

# Todo
The project requires a corpus, we will be using the **Google News** corpus which can be downloaded [here](https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit?resourcekey=0-wjGZdNAUop6WykTtMip30g). Once you've downloaded the file, follow the instructions below:
- Use an archiving tool(we recommend winrar) to extract the file into `BCJ-AI-API`
- rename the file to `google_news.bin`
- open python in command line and run the following commands: 
   - `import nltk`
   - `nltk.download('stopwords')`
   - `exit()`
- then finally run the program: `python run.py` to create the word vectors

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
    * The token appears in a new file called ``.env``
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

## Script Listener

Since we used JIRA as the database the front end talks to, we decided to have JIRA be able to talk to the Consolidation Server in the form of HTTP methods. We used a Script Listener for this. Script Listeners can be made to trigger when certain events happen like e.g. issues being created, updated, or deleted. Script Listener scripts are written in `Groovy`. Documentation for Script Listeners can be found here: https://docs.adaptavist.com/sr4jc/current/features/script-listeners.

Below can be seen the code we made for our Script Listener

```groovy

def summary = issue.fields.summary
def description = issue.fields.description
def issueKey = issue.key
def id = issue.id
def created = issue.fields.created
baseUrl = "<your-url>" //This is the URL the Listener will do its queries on. 

if(issue_event_type_name == "issue_created") {
    def response = post("/bug") // Ends up posting on <your-url>/bug
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer " + "<your-token>")
        .body(
            [
                summary: summary,
                description: description,
                structured_info: [
                        id: id,
                        date: created
                    ]
            ]
          )
        .asJson()
}
else if(issue_event_type_name == "issue_updated") {
    def response = patch("/bug")
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer " + "<your-token>")
        .body(
            [
                summary: summary,
                description: description,
                structured_info: [
                        id: id,
                        date: created
                    ]
            ]
          )
        .asJson()
}
else {
    def response = delete("/bug")
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer " + "<your-token>")
        .body(
            [
                id: id
            ]
          )
        .asJson()
}

```