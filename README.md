# Artificial intelligence API for BCJ
Artificial Intelligence API for usability problems. 

## Web service
* `/bug`
  * `GET` query the **k** most similar bugs
  * `POST` insert a bug 
    * summary and description must be string values, may be empty strings. id must be a number or a number in string format, creationDate must be a string in the following format: YYY-MM-DD. At least one of the keys must contain valid information for successful insertion. `{
   "summary": "summary",
   "description": "description,
   "structured_info": {id, creationDate}
 }` 
  * `DELETE` delete a bug 
  * `PATCH` update a bug 
* `/bug-batch`
  * `POST` insert k bugs 
  * `DELETE` delete k bugs 
  

