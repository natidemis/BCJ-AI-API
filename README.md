# Artificial intelligence API for BCJ
Artificial Intelligence API for usability problems. 

## Web service
* `/bug`
  * `GET` query the **k** most similar bugs
  * `POST` insert a bug 
    * data format: `{
   "summary": "summary",
   "description": "description,
   "structured_info": {id, creationDate}
 }` 
  * `DELETE` delete a bug 
  * `PATCH` update a bug 
* `/bug-batch`
  * `POST` insert k bugs 
  * `DELETE` delete k bugs 
  

