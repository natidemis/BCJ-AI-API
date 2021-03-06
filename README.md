# Artificial intelligence API for [Bug-Consolidator-for-Jira](https://github.com/Hallinn/Bug-Consolidator-for-Jira)
Artificial Intelligence API for usability problems.

***

## Authors

- Kristófer Ásgeirsson - `kra33`
- Marcelo Felix Audibert - `Gitcelo`
- Natanel Demissew Ketema - `natidemis`

***
## Project versions
* Main branch (fastAPI)
* flask-version branch (flask)


The first version of the project used [`flask`](https://flask.palletsprojects.com/en/2.0.x/) as a web framework which made sense at first but with further investigation, it became clear that [`fastAPI`](https://fastapi.tiangolo.com/) satisfied our needs better. As we were deploying the flask app using `gunicorn`, some unwanted problems presented themselves, although solvable, it was a good enough reason to look into `FastAPI`.

### What the project needed to accomplish
1. Needed to validate JSON data from client
2. Needed to store data. Solved using `postgreSQL` through the [`asyncpg`](https://magicstack.github.io/asyncpg/current/) package due to its speed as shown [here](https://github.com/MagicStack/asyncpg).

Task nr.1 was solved using [`schema`](https://pypi.org/project/schema/) json validator which made reading the code more difficult than necessary.
Task nr.2 required [`asyncio`](https://docs.python.org/3/library/asyncio.html) to create coroutines for the asyncronous database tasks required by `asyncpg`

### Why fastAPI?
#### Fully asyncronous
Making it fully asyncronous meant that a client could send multiple requests and receive responses in subsequent responses as opposed to a syncronous request where the response is returned to the same HTTP connection as the request.

Another benefit was that relying on `asyncio` to create coroutines for `asyncpg` was no longer necessary. Using the async benefits of `FastAPI`, it was just a simple task of
chaining a bunch of coroutines together and allowing `FastAPI` to handle it.

#### Validates json data on request
`FastAPI` was developed alongside [`pydantic`](https://pydantic-docs.helpmanual.io/) for validation purposes and using the `BaseModel` class from pydantic made for some easily readable code that can validate the clients json data on request.
***
## Requirements

* [`up_utils`](https://github.com/kra33/up-utils) is a submodule that implements its own version of scipy's [KDTree](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html) and its own word embedder using either `commoncrawl` or `google news` vectors.
  * Follow the instructions provided and install the package.
* `Models` is a `tensorflow.keras.models` saved using the `models.save_model()` method.
  * Used for encoding the word embeddings provided by `up_utils`'s `Word2Vec.get_sentence_matrix`
  * Needs to be stored in the root directory of this project re-named as `"Models"`
    * `Models` won't be compiled so providing its weights is unnecessary.


***
## Setup - locally

### The API itself
- Install python 3.8.10
   *  other versions may or may not work.
- Install dependencies by writing ``pip install -r requirements.txt`` into terminal
    * Note that the versions in the file may be outdated
- If the above step failed to properly install all packages, install pipenv by writing `pip install pipenv` into the terminal and then run `pipenv install` to install using the pipfile
   * Note that if both steps fail, it may be worth trying to remove the specified versions of some of the packages to install their latest versions.
    
- Run `setup.py` to generate a secret token and install the google_news bin file.
    * The token appears in the enviroment file ``.env``
    * The token has to be in header as bearer token when making HTTP requests to the server
- Resetting the database on startup
  - To reset the database, simply add `RESET=True` in `.env` 
- Start the app locally with `uvicorn main:app`
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

## Setup - Linux (Fedora operating system)

### Setting up the production enviroment

**Uvicorn and Gunicorn**

The packages Uvicorn and Gunicorn were used in tandem to run the server. The command used for start-up is

 `gunicorn -t 1000 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8008 main:app`

 The command makes the server listen to port 8008 and makes it time out if it hasn't been able to fullly start up after 1000 seconds. The command can be modified as needed.

 **NGINX**

 NGINX is an HTTP and reverse proxy server. The reason NGINX was used with Uvicorn and Gunicorn is that the latter two packages are not made to be front-facing. They are easy to DOS and overwhelm and NGINX is generally better at being a web server. NGINX listens to port 80 and forwards requests to the Uvicorn/Gunicorn server if it thinks they should be forwarded there based on the configurations made on it. Below can be seen how NGINX was set up on the Fedora system:
 
 * Install NGINX using the command `sudo dnf install nginx`

 * Run the commands `sudo systemctl enable nginx` and `sudo systemctl start nginx` to enable and start the service

 * Open the firewall for NGINX by running the commands `sudo firewall-cmd --permanent --add-service=http` and `sudo firewall-cmd --pemanent --add-service=https` and then reloading firewalld by running `sudo firewall-cmd --reload`

 * Make the directories `sites-available` and `sites-enabled` in the directory /etc/nginx

 * Open the file nginx.conf in /etc/nginx and add the following to the bottom of the http block `include /etc/nginx/sites-enabled/*`

 * cd into the directory /etc/nginx/sites-available and create a file which here will be referred to as `bcj-server` but the name can be anything

 * Open the file bcj-server and write the following into it:

 ```

server {
    listen 80;
    server_name <the server's network address>;

    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
        proxy_pass http://127.0.0.1:8008;
    }
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream uvicorn {
    server unix:/tmp/uvicorn.sock;
}

 ```

 * Run the command `sudo nginx -t` to make sure that the syntax of bcj_server is ok

 * After the syntax of bcj-server passes the test, create a symlink of the file in the sites-enabled directory by running the command `sudo ln -s /etc/nginx/sites-available/bcj-server /etc/nginx/sites-enabled/` and then run the command `sudo ls -l /etc/nginx/sites-enabled/` to see if the symlink has been created

 * Run `sudo systemctl restart nginx` so the configuration of NGINX takes place

 * SELinux may ban NGINX from forwarding HTTP requests to the Uvicorn/Gunicorn app. If that happens, run either of the commands `sudo setsebool httpd_can_network_relay 1` or `sudo setsebool httpd_can_network_connect 1`

### Running the server with systemd

Always running the server in terminal can be a nuisance. A solution for this is making a systemd script which can be run in the background. Here are the instructions for the script:

* cd to /etc/systemd/system and make a new file called `<name-for-file>.service`. From here on the file will be referred to as `bcj.service`

```shell
[Unit]
Description=Gunicorn instance to serve the backend of the Bug Consolidation for JIRA
After=network.target

[Service]
User=<user-that-runs-the-server>
Group=nginx
WorkingDirectory=/path/to/server/directory
Environment="PATH=/path/to/virtual/environment/bin/directory"
ExecStart=/path/to/.sh/file
Restart=always

[Install]
Wanted=multi-user.target
```

* The .sh file referred to in ExecStart contains the script below:

```shell
#!/bin/bash
source /path/to/virtual/environment/bin/activate
gunicorn -t 1000 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8008 main:app
```

* Now run the commands `sudo systemctl enable bcj` and `sudo systemctl start bcj`, where bcj stands for the file bcj.service

* To check if the server is running run the command `sudo systemctl status bcj`

### Postgres
* Check all available DNF modules for postgresql by running `sudo dnf module list postgresql`

* Enable the repository for postgresql for a specific version by using <br />`sudo dnf module enable postgresql:<version>`

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
The project requires a corpus. We used the **Google News** corpus which can be found [here](https://github.com/mmihaltz/word2vec-GoogleNews-vectors). Once the file is downloaded, an archiving tool (we recommend winrar) should be used to extract the file into the `BCJ-AI-API` folder.
- The **Google News** vectors can be downloaded by executing `setup.py`

The **CommonCrawl** corpus can be used as an alternative. It can be found [here](https://nlp.stanford.edu/projects/glove/).

***

## NLTK


The NLTK package should install itself with stopwords if it isn't already installed. If it doesn't install itself,write the following into a python console:

```
>>> import nltk
>>> nltk.download('stopwords')
>>> exit()
```
***

## Git hook

* In this project the server was set up on a Linux computer. The server directory pulled from a bare git repo local to the Linux computer

* A git hook was made that would fire every time commits were pushed to the Linux repo to right afterwards pull into the server directory and then restart the server

* The hook was made by cd-ing into the directory hooks directory under the bare repo directory and creating the file `post-receive`

* Into the file post-receive the following script was put:

```shell
!#/usr/bin/sh

TARGET="/path/to/server"
GIT_DIR="path/to/bare/git/repo"
BRANCH="main" # Can be any other branch

while read oldrev newrev ref
do
         # Only checking out main
         if [[ $ref = refs/heads/"$BRANCH" ]];
         then
               echo "Ref $ref received. Deploying ${BRANCH} branch to production..."
               git --work-tree="$TARGET" --git-dir="$GIT_DIR" checkout -f $BRANCH
               echo "Restarting server..."
               sudo /usr/bin/systemctl restart bcj
         else
               echo "Ref $ref received. Doing nothing: only the ${BRANCH} branch may be deployed on this server"
         fi
done
```
* If the user that is used to run the server requires a password to run sudo commands, run the command `sudo visudo`. This opens up the file in /etc/sudoers. Add the following to the document: `<name-of-user-that-needs-sudo-rights> ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart <name-of-server>`

* The command above allows the user that runs the server to run the command systemctl restart in sudo without requiring a password and only that command 

* \<name-of-server> refers to the name of the .service file used to run the server, i.e. \<name-of-server>.service

* Note that if the git hook 

***
## Example of HTTP request to server made in Python

```python
import requests

url = "<your-url>/bug"
token = "my bearer token"
json = {
    "user_id": "1",
    "summary": "summ",
    "description": "desc",
    "structured_info": {
        "id": 1,
        "batch_id": 1,
        "date": "2015-02-28"
    }
}

response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(token)},json = json)
```

***

## Web service
#### Information on how to use the webservice should also be available on '/docs' once the server is up and running.
* `/bug`
  * `GET` query the **k** most similar bugs for the given `user_id`
      * given a value `k`, return the 'k' most similar from the database, default is 5. 
      *  Either `summary` or `description` must be included. Both preferably. `date` -string in  `YYYY-MM-DD` format.
      ```JSON
      {
         "user_id": "string",
         "summary": "string",
         "description": "string",
         "structured_info": {
                "date": "YYYY-MM-DDD"
         },
         "k"(optional): int
      }
      ``` 
    * Response: a list, "id" with all ids ordered from the most similar to least similar. "dist", a list with the distance values for each ID
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
      * `user_id` must be an int, stores the given data for this `user_id`. May or may not exist in the database.
      * summary and description must be string values, either summary or description may be empty but not both.
      * Structured_info must be valid for insertion and must contain the following:
         *  id, an integer and unique in the database.
         *  date, a string in the format `YYYY-MM-DD`
         *  batch_id(optional, not required), an integer for the purposes of grouping a set of bugs together, most useful for deleting a group of bugs at once.
      ```JSON
      {
        "user_id": "string",
        "summary": "string",
        "description": "string",
        "structured_info": {
          "id": int,
          "date": "YYYY-MM-DD",
          "batch_id"(optional): int
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
     * key-value pairs as discussed above.
     ```JSON
     {
          "user_id": "string",
          "id": int
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
        "user_id": "string",
        "summary"(optional): "string",
        "description"(optional): "string",
        "structured_info": {
          "id": int,
          "date": "YYYY-MM-DD",
          "batch_id"(optional): int
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
  * `POST` insert n bugs 
      * Batch insert similar to `post` on `/bug`
      * for each bug, the json oject passed must be in the same format as specified for `post` on `/bug`
      * All n bugs must have the same `batch_id`, batch_id is a requirement. `**` implies they must be the same.
      * `^` implies that those values must be unique. In this case, all given ids must be unique for each data for a given particular user.
      ```JSON
      {
        "user_id": "string",
        "data": [
            {
                "summary": "string",
                "description": "string",
                "structured_info": {
                    "id": int^,
                    "date": "YYYY-MM-DD",
                    "batch_id"(required): int**
                }
            },
            {
            	  "summary": "string",
                "description": "string",
              "structured_info": {
                  "id": int^,
                   "date": "YYYY-MM-DD",
                   "batch_id"(required): int**
                 }
            }
        ]
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
  * `DELETE` delete n bugs(a batch)
      ```JSON
      {
         "user_id": "string,
         "batch_id": int
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

Since JIRA was used as the database the front end talks to, it was decided to have JIRA be able to talk to the Consolidation Server in the form of HTTP requests. The Atlassian app Script Listener was used for this. Script Listeners can be made to trigger when certain events happen like e.g. issues being created, updated, or deleted. Script Listener scripts are written in `Groovy`. Documentation for Script Listeners can be found here: https://docs.adaptavist.com/sr4jc/current/features/script-listeners.

The expression evaluated was 
```groovy
true
```

and the event the Script listener listened for was `Issue Created` 

Below can be seen the Script Listener code itself:

```groovy
def baseUrl = "<url>" 
            
def response = post("${baseUrl}/bug")
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer " + "<token>")
        .body(
            [
            user_id: (user['accountId']),
            summary: (issue.fields.summary),
            description: (issue.fields.description),
            structured_info: [
                    date: (issue.fields.created.substring(0,10)),
                    id: (issue.id)
                    ]
            ]
        )
        .asObject(Map)
```
