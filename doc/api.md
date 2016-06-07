# Riker REST API
*api.rikerproject.com*
## User Actions
#### Login
- method: **POST**
- endpoint: *api.rikerproject.com/login*
- params:
	- `userId`: String
	- `password`: String
- response:
	- success:
		- code: 200
		- content: N/A
	- failure:
		- code: 401
		- content: { `errorMsg`: String }

- description: Authenticates user and begins a session.

#### Register
- method: **POST**
- endpoint: *api.rikerproject.com/register*
- params:
	- `userID`: String
	` `password`: String
- response:
	- success:
		- code: 200
		- content: N/A
	- failure:
		- code: 400
		- content: { `errorMsg`: String }

- description: Creates a user account and begins a session.

## Resource Requests

#### Problems
- method: **GET**
- endpoint: *api.rikerproject.com/problems*
- params:
	- `problemID`: Int
	- `userID`: String
	- `limit`: Int
- response:
	- success: 
		- code: 200
		- content: [ { `problemID`: Int, `userID`: String, `submissionTime`: Int, `title`: String, `prompt`: String }, ... ]
	- failure (bad request)
		- code: 400
		- content: { errorMsg: String }

- description: Retrieves a list of problem submissions. Optionally filter by `userID` or `problemID` (this will only generate 0 or 1 results). `limit` specifies maximum result count. Results are sorted by `submissionTime` (Unix UTC). `prompt` is in markdown format. 

#### Solutions
- method: **GET**
- endpoint: *api.rikerproject.com/solutions*
- params:
	- `solutionID`: Int
	- `problemID`: Int
	- `userID`: String
	- `language`: String
	- `validatedOnly`: Boolean
	- `limit`: Int
- response:
	- success: 
		- code: 200
		- content: [ { `solutionID`: Int, `problemID`: Int, `userID`: Int, `submissionTime`: Int, `title`: String, `language`: String, `source`: String, `validation`: String }, ... ]
	- failure (bad request)
		- code: 400
		- content: { errorMsg: String } 

- description: Retrieves a list of solutions. Optionally filter by `problemID`, `userID`, `language`, or `solutionID` (this will only generate 0 or 1 results). `validatedOnly` specifies whether solution must be validted. `limit` specifies maximum result count. Results are sorted by `submissionTime` (Unix UTC).

#### Comments
- method: **GET**
- endpoint: api.rikerproject.com/comments
- params:
	- `referenceID`: Int
	- `referenceType`: String		-- *"problem"|"solution"*
	- `userID`: String
	- `limit`: Int
- response
	- success:
		- code: 200
		- content: [ { `userID`: String, `submissionTime`: String, `body`: String }, ... ]
	- failure (bad request)
		- code: 400
		- content: { errorMsg: String }

- description: Retrieves comments for the specified submission. Filter results by `userID` or `referenceID` (this will only generate 0 or 1 results). `referenceID` is either a problemID or solutionID depending on the value of `referenceType`. `limit` specifies maximum result count.

## Resource Submissions

#### Problems
- method: **POST**
- endpoint: *api.rikerproject.com/problems*
- params:
	- `title`: String
	- `prompt`: String		-- *Parsed as markdown.*
	- `testInput`: String
	- `testOutput`: String
	- `timeout`: Int		-- *In seconds. Must be between 1 and 10 seconds.*
- response:
	- success:
		- code: 200
		- content: N/A
	- failure (not logged in):
		- code: 401
		- content: { `errorMsg`: String }
	- failure (bad submission): 
		- code: 400
		- content: { `errorMsg`: String }

- description: Submits a problem. **This method requires an active session**. 

#### Solutions
- method: **POST**
- endpoint: *api.rikerproject.com/solutions*
- params:
	- `problemID`: Int
	- `title`: String
	- `language`: String
	- `source`: String
- response:
	- success:
		- code: 200
		- content: N/A
	- failure (not logged in):
		- code: 401
		- content: { `errorMsg`: String }
	- failure (bad submission): 
		- code: 400
		- content: { `errorMsg`: String }

- description: Submits a solution to problem with id `problemID`. **This method requires an active session**. 

#### Comments
- method: **POST**
- endpoint: *api.rikerproject.com/comments*
- params:
	- `referenceID`: Int
	- `referenceType`: String		-- *"problem"|"solution"*
	- `body`: String
- response:
	- success:
		- code: 200
		- content: N/A
	- failure (not logged in):
		- code: 401
		- content: { `errorMsg`: String }
	- failure (bad submission):
		- code: 400
		- content: { `errorMsg`: String }

- description: Submits a comment to the problem or solution (depending on `referenceType`) with id `referenceID`. **This method requires an active session**