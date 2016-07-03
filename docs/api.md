# Riker REST API
*api.rikerproject.com*

## User Actions

#### Register
- method: **POST**
- endpoint: *api.rikerproject.com/register*
- params:
	- `userId`: String
	- `password`: String
- response-body: N/A
- description: 
	Creates a user account.

#### CreateSession
- method: **POST**
- endpoint: *api.rikerproject.com/create-session*
- params:
	- `userId`: String
	- `password`: String
- response-body:
	```
	{ 
		userId: String,
		sessionKey: String, 
		expiration: String
	}
	```
- description:
	Create a 30-day api session for `userId`.
	All resource submissions/edits/removals require a valid session key.
	Unauthroized submission/edits/removals will recieve error code `401` (see **Errors**).
		
#### EndSession
- method: **POST**
- endpoint: *api.rikerproject.com/end-sesson*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Expires `sessionKey`.
	

## Resource Requests

#### Problems
- method: **GET**
- endpoint: *api.rikerproject.com/problems*
- response-body: 
	```
	[{ 
		problemId: Int, 
		userId: String, 
		submissionTime: Int, 
		title: String, 
		prompt: String 
	}]
	```
- description: 
	Retrieves problems ordered by `submissionTime`. 

#### ProblemById
- method: **GET**
- endpoint: *api.rikerproject.com/problems/<problem_id>*
- response-body: 
	```
	{ 
		problemId: Int, 
		userId: String, 
		submissionTime: Int, 
		title: String, 
		prompt: String 
	}
	```
- description:
	Retrieves `problemId`. 

#### Solutions
- method: **GET**
- endpoint: *api.rikerproject.com/problems/<problemId>/solutions*
- response-body:
	```
	[{ 
		solutionId`: Int, 
		userId`: Int, 
		submissionTime`: Int, 
		problemId`: Int, 
		language: String, 
		source: String, 
		validation: String 
	}]
	```
- description: 
	Retrieves solutions for `problemId` ordered by `submissionTime`.

#### SolutionById
- method: **GET**
- endpoint: *api.rikerproject.com/solutions/<solutionId>*
- response-body:
	```
	{ 
		solutionId: Int, 
		userId: Int, 
		submissionTime: Int, 
		problemId: Int, 
		language: String, 
		source: String, 
		validation: String 
	}
	```
- description:
	Retrieves `solutionId`. 

#### ProblemComments
- method **GET**
- endpoint: *api.rikerpoject.com/problems/<problemId>/comments*
- response-body:
	```
	[{
		problemCommentId: String,
		userId: String,
		submissionTime: String,
		problemId: Int,
		body: String
	}]
	```
- description:
	Retrieves comments for `problemId`.

#### ProblemCommentsById
- method: **GET**
- endpoint: *api.rikerproject.com/problems/comments/<problemCommentId>*
- response-body:
	```
	{
		problemCommentId: String,
		userId: String,
		submissionTime: String,
		problemId: Int,
		body: String
	}
	```
- description:
	Retrieves `problemCommentId`.

#### SolutionComments
- method **GET**
- endpoint: *api.rikerpoject.com/solutions/<solutionId>/comments*
- response-body:
	```
	[{
		solutionCommentId: String,
		userId: String,
		submissionTime: String,
		solutionId: Int,
		body: String
	}]
	```
- description:
	Retrieves comments for `solutionId`.

#### SolutionCommentsById
- mehtod: **GET**
- endpoint: *api.rikerproject.com/solutions/comments/<solutionCommentId>*
- response-body:
	```
	{
		solutionCommentId: String,
		userId: String,
		submissionTime: String,
		solutionId: Int,
		body: String
	}
	```
- description:
	Retrieves `solutionCommentId`.

#### Users
- method **GET**
- endpoint: *api.rikerproject.com/users*
- response-body:
	```
	{
		userId: String,
		creationTime: String
	}
	```
- description:
	Retrieves a list of all registered users. 

#### UserById
- method **GET**
- endpoint: *api.rikerproject.com/user/<userId>*
- response-body:
	```
	{
		userId: String,
		creationTime: String,
		problemIds: [Int],
		solutionIds: [Int],
		problemCommentIds: [Int],
		solutionCommentIds: [Int]
	}
	```
- description:
	- Retrieve information about and submissions by `userId`. 
	- Submission ids are ordered by submission time.

## Resource Submissions

#### Problems
- method: **POST**
- endpoint: *api.rikerproject.com/problems*
- params:
	- sessionKey: String
	- title: String
	- prompt: String	
	- testInput: String
	- testOutput: String
	- timeout: Int		
- response-body: N/A
- description: 
	Submits a problem. `timeout` is in seconds.

#### Solutions
- method: **POST**
- endpoint: *api.rikerproject.com/solutions*
- params:
	- sessionKey: String
	- problemId: Int
	- language: String
	- source: String
- response-body: N/A
- description: 
	Submits a solution to problem with id `problemId`.

#### ProblemComment
- method: **POST**
- endpoint: *api.rikerproject.com/problems/<problemId>/comments*
- params:
	- `sessionKey`: String
	- `body`: String
- response-body:
	```
	{
		problemCommentId: Int
	}
	```
- description:
	Submits a comment for `problemId`.

#### SolutionComment
- method: **POST**
- endpoint: *api.rikerproject.com/solutions/<solutionId>/comments*
- params:
	- `sessionKey`: String
	- `body`: String
- response-body:
	```
	{
		problemCommentId: Int
	}
	```
- description:
	Submits a comment for `problemId`. 


## Resource Editing

#### EditProblem
- method: **PUT**
- endpoint: *api.rikerproject.com/problems/<problemId>/edit*
- params:
	- `sessionKey`: String
	- `title`: String
	- `prompt`: String	
	- `testInput`: String
	- `testOutput`: String
	- `timeout`: Int		
- response-body: N/A
- description:
	Updates the fields of `problemId`.

#### EditSolution
- method: **PUT**
- endpoint: *api.rikerproject.com/solutions/<solution_id>*
- params:
	- `sessionKey`: String
	- `language`: String
	- `source`: String
- response-body: N/A
- description:
	Updates the fields of `solutionId`.

#### EditProblemComment
- method: **PUT**
- endpoint: *api.rikerproject.com/problems/comments/<problemCommentId>*
- params:
	- `sessionId`: String
	- `body`: String
- response-body: N/A
- description:
	Updates contents of `problemCommentId`.
	
#### EditSolutionComment
- method: **PUT**
- endpoint: *api.rikerproject.com/solutions/comments/<solutionCommentId>*
- params:
	- `sessionId`: String
	- `body`: String
- response-body: N/A
- description:
	Updates contents of `problemCommentId`.
	

## Resource Removal

#### RemoveProblem
- method: **DELETE**
- endpoint: *api.rikerproject.com/problems/<problemId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `problemId` and all associated solutions/comments.

#### RemoveSolution
- method: **DELETE**
- endpoint: *api.rikerproject.com/solutions/<solutionId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `solutionId` and all associated comments.

#### RemoveProblemComment
- method: **DELETE**
- endpoint: *api.rikerproject.com/problems/comments/<problemCommentId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `problemCommentId`.

#### RemoveSolutionComment
- method: **DELETE**
- endpoint: *api.rikerproject.com/solutions/comments/<solutionCommentId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `solutionCommentId`. 


## Errors

Non-200 responses will have the following format: 

- response-codes:
	- `400`: Malformed or invalid request.
	- `401`: Authentication error (invalid credientials or session key).
	- `404`: Resource not found.
- response-body:
	```
	{
		errorMsg: String
	}
	```

