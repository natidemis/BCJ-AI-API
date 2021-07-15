# Artificial intelligence API for BCJ
Artificial Intelligence API for usability problems.

***
## Authors

- Kristófer Ásgeirsson - `kra33`
- Marcelo Felix Audibert - `Gitcelo`
- Natanel Demissew Ketema - `natidemis`

***

## ToDo

* Remove the drop table functionality
* Send JSON error if id is already in table. As is we only send a 500 error with the message
* Update Corpus part to incorporate CommonCrawl

***

## Setup - locally


### The api itself
- Install python 3.8.10
   *  other versions may or may not work.
- Install dependencies by writing ``pip install -r requirements.txt`` into terminal
    * Note that the versions in the file may be outdated
- If the above step failed to properly install all packages, install pipenv by writing `pip install pipenv` into the terminal and then run `pipenv install` to install using the pipfile
   * Note that if both steps fail, it may be worth trying to remove the specified versions of some of the packages to install their latest versions.
    
- Run `gentoken.py` to generate a secret token
    * The token appears in a new file called ``.env``
    * The token has to be in header as bearer token when making HTTP requests to the server

### Postgres
* Install postgresql [here](https://www.google.com/search?q=install+postgresql&oq=install+postgresql&aqs=chrome.0.69i59j35i39j0j0i20i263j0l2j69i60l2.2572j0j7&sourceid=chrome&ie=UTF-8) along with [pgadmin4](https://www.pgadmin.org/download/) in order to manage the database interactively.

    * CLI is also an option. A handful of tutorials should be available online.
* During the installation process, postgresql will require a password for the superuser, `postgres`. A password which I will reference as `<postgres_password>`.

    *  Creating other users with specific roles using pgadmin4 is also an option.
        * `Open pgadmin4 --> login using password --> Click 'server' --> right click 'login/roles' --> create login/role`  

* The final step is then to create a database: `open pgadmin4 --> login using <postgres_password> --> click Servers --> right click 'Databases' --> Create Databases`, give it a name which will be referenced as `<Database_name>`.

* Put the following in the `.env` file: `DATABASE_URL = "postgres://postgres:<postgres_password>@localhost/<Database_name>"`
    * The second `postgres` in the url is replacable by any user as long as that user has the approperiate role to manage the database and `<postgres_password>` can be replaced by the password given to that user. 
***

## Setup - linux(fedora operating system)
### Setting up the production enviroment
* Blah blah blah

### Postgres
* Check all available DNF modules for postgresql by running `sudo dnf module list postgresql`

* Enable the repository for postgresql for a specific versing by using <br />`sudo dnf module enable postgresql:<version>`

* Install the module: `sudo dnf install postgresql-server`

* Initialize the database: `sudo postgresql-setup --initdb`

* Start the service by running `sudo systemctl enable postgresql` and then `sudo systemctl start postgresql`

* The superuser `postgres` needs a new password so run `sudo passwd postgres` and give the superuser a new password which will be referenced as `<postgres_password>` in the following steps

* Run `su - postgres -c "psql"` to access the CLI using `<postgres_password>`

* Create a database using `CREATE DATABASE <database_name>`

* All the pieces should now be there and the final step is to include the following in the `.env` file: <br /> `DATABASE_URL = "postgres://postgres:<postgres_password>@localhost/<database_name>"`

* If other issues occur, the steps found [here](https://tecadmin.net/how-to-install-postgresql-and-pgadmin-in-fedora/) may be worth a try

***


## Corpus
The project requires a corpus. We used the **Google News** corpus which can be downloaded [here](https://github.com/mmihaltz/word2vec-GoogleNews-vectors). Once you've downloaded the file, use an archiving tool (we recommend winrar) to extract the file into the `BCJ-AI-API` folder.

**CommonCrawl**: https://nlp.stanford.edu/projects/glove/

***

## Run

Run the file run.py to start the server (e.g. by writing ``python run.py`` in terminal).

The pacakge NLTK should install itself with stopwords if it isn't already installed. If it doesn't install itself, either run `stopwords.py` or write the following into a python console:

```
>>> import nltk
>>> nltk.download('stopwords')
>>> exit()
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
      *  Summary and description are required. date, string in the form `YYYY-MM-DD`.
      ```JSON
      {
         "summary": "summary",
         "description": "description,
         "structured_info": {
                "date": "YYYY-MM-DDD"
         }
      }
      ``` 
    * Response: a list, "id" with all ids ordered from the closest to the farthest. "dist", a list with the distance values for each ID
        * Example:
        ```JSON
         {
            "data": {
                "dist": [
                    0.0,
                    0.05297874857599651,
                    0.05297874857599651,
                    0.05297874857599651
                ],
                "id": [
                    4,
                    3,
                    2,
                    1
                ]
            }
         }
         ```
  * `POST` insert a bug 
    * Data requirement for request in JSON format:
      * summary and description must be string values, either summary or description may be empty but not both.
      * Structured_info must be valid for insertion and must contain the following:
         *  id, an integer and unique in the database.
         *  date, a string in the format `YYYY-MM-DD`
         *  batch_id(optional, not required), an integer for the purposes of grouping a set of bugs together, most useful for deleting a group of bugs at once.
      ```JSON
      {
        "summary": "summary",
        "description": "description",
        "structured_info": {
          "id": 1,
          "date": "YYYY-MM-DD",
          "batch_id"(optional): 1
          }
        }
        ```
         * Response: status code, json object, that may explain the status response.
         ```JSON
         {
            "data": {
               "message": "message"
            }
         }
         
         ```

  * `DELETE` delete a bug 
     * valid id in the format: 
     ```JSON
     {
          "id": 1 
     }
     ```
     * Response: status code, json object, that may explain the status response.
         ```JSON
         {
            "data": {
               "message": "message"
            }
         }
         
         ```
  * `PATCH` update a bug 
      * summary and description are optional, structured info, mainly id and date are required.
      ```JSON
      {
        "summary"(optional): "summary",
        "description"(optional): "description",
        "structured_info": {
          "id": 1,
          "date": "YYYY-MM-DD",
          "batch_id"(optional): 1
          }
       }
      ```
      * Response: status code, json object, that may explain the status response.
         ```JSON
         {
            "data": {
               "message": "message"
            }
         }
         
         ```
      
* `/batch`
  * `POST` insert k bugs 
      * Most similar to the `post` on `/bug`
      * for each bug, the json oject passed must be in the same format as specified for `post` on `/bug`
      * All k bugs must have the same `batch_id`, batch_id is a requirement.
      ```JSON
      [
         {
        "summary": "summary",
        "description": "description",
        "structured_info": {
          "id": 1,
          "date": "YYYY-MM-DD",
          "batch_id"(required): 1
          }
        },
        {
        "summary": "summary",
        "description": "description",
        "structured_info": {
          "id": 2,
          "date": "YYYY-MM-DD",
          "batch_id"(required): 1
          }
        }
      ]
      ```
      * Response: status code, json object, that may explain the status response.
        ```JSON
         {
            "data": {
               "message": "message"
            }
         }
         
         ```
  * `DELETE` delete k bugs(a batch)
      ```JSON
      {
         "batch_id": 1
      }
      ```
      * Response: status code, json object, that may explain the status response.
         ```JSON
         {
            "data": {
               "message": "message"
            }
         }
         
         ```
  
***

## Script Listener

Since we used JIRA as the database the front end talks to, we decided to have JIRA be able to talk to the Consolidation Server in the form of HTTP methods. We used a Script Listener for this. Script Listeners can be made to trigger when certain events happen like e.g. issues being created, updated, or deleted. Script Listener scripts are written in `Groovy`. Documentation for Script Listeners can be found here: https://docs.adaptavist.com/sr4jc/current/features/script-listeners.

The expression we evaluated was 
```groovy
issue.issueType.name == 'Bug'
```

Below can be seen the Script Listener code itself

```groovy

def summary = issue.fields.summary 
def description = issue.fields.description
def issueKey = issue.key
def id = issue.id
def created = issue.fields.created
baseUrl = "<your-url>" //This is the URL the listener will do its queries on

if(issue_event_type_name == "issue_created") {
    def response = post("/bug") //Ends up posting on <your-url>/bug
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
