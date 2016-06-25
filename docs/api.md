# Riker REST API
*api.rikerproject.com*

## User Actions

#### Register
- method: **POST**
- endpoint: *api.rikerproject.com/register*
- params:
	- `userId`: String
	- `password`: String
- description: 
	Creates a user account and begins a session.

#### CreateSession
- method: **POST**
- endpoint: *api.rikerproject.com/create-session*
- params:
	- `userId`: String
	- `password`: String
- response-body:
	{ 
		`userId`:  String,
		`sessionKey`: String, 
		`expiration`: String
	}
- description:
	Create a 30-day api session for `userId`.
	
		
#### EndSession
- method: **POST**
- endpoint: *api.rikerproject.com/end-sesson*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Expires `sessionKey`
	

## Resource Requests

#### Problems
- method: **GET**
- endpoint: *api.rikerproject.com/problems*
- response-body: 
	[{ 
		`problemID`: Int, 
		`userId`: String, 
		`submissionTime`: Int, 
		`title`: String, 
		`prompt`: String 
	}]
- description: 
	Retrieves problems ordered by `submissionTime`. 

#### ProblemSolutions
- method: **GET**
- endpoint: *api.rikerproject.com/problems/<problemId>/solutions*
- params:
- response-body:
	[{ 
		`solutionID`: Int, 
		`userId`: Int, 
		`submissionTime`: Int, 
		`problemID`: Int, 
		`title`: String, 
		`language`: String, 
		`source`: String, 
		`validation`: String 
	}]
- description: 
	Retrieves solutions for `problemId` ordered by `submissionTime`.

#### ProblemComments
- method **GET**
- endpoint: *api.rikerpoject.com/problem/<problemId>/comments*
- response-body:
	[{
		`userId`: String,
		`submissionTime`: String,
		`problemId`: Int,
		`body`: String
	}]
- description:
	Retrieves comments for `problemId`.

#### SolutionComments
- method **GET**
- endpoint: *api.rikerpoject.com/solutions/<solutionId>/comments*
- response-body:
	[{
		`userId`: String,
		`submissionTime`: String,
		`solutionId`: Int,
		`body`: String
	}]
- description:
	Retrieves comments for `solutionId`.

#### User
- method **GET**
- endpoint: *api.rikerproject.com/user/<userId>*
- response-body:
	{
		`userId`: String,
		`creationTime`: String
	}
- description:
	Retrieve information about `userId`.

#### UserProblems
- method **GET**
- endpoint: *api.rikerproject.com/user/<userId>/problems* 
- response-body:
	[{ 
		`problemID`: Int, 
		`userId`: String, 
		`submissionTime`: Int, 
		`title`: String, 
		`prompt`: String 
	}]
- description:
	Retrieves problems submitted by `userId` ordered by `submissionTime`.
	
#### UserSolutions
- method: **GET**
- endpoint: *api.rikerproject.com/user/<userId>/solutions*
- response-body:
	[{
		`solutionID`: Int, 
		`userId`: Int, 
		`submissionTime`: Int, 
		`problemID`: Int, 
		`title`: String, 
		`language`: String, 
		`source`: String, 
		`validation`: String 
	}]
- description:
	Retrieves solutions submitted by `userId` ordered by `submissionTime`.

#### UserProblemComments
- method: **GET**
- endpoint: *api.rikerproject.com/user/<userId>/problem-comments*
- response-body:
	[{
		`userId`: String,
		`submissionTime`: String,
		`problemId`: Int,
		`body`: String
	}]
- description:
	Retrieves problem comments for `problemId` submitted by `userId` ordered by `submissionTime`.

#### UserSolutionComments
- method **GET**
- endpoint: *api.rikerproject.com/user/<userId>/solution-comments*
- response-body:
	[{
		`userId`: String,
		`submissionTime`: String,
		`solutionId`: Int,
		`body`: String
	}]
- description:
	Retrieves solution comments for `solutionId` by `userId` ordered by `submissionTime`.


## Resource Submissions

- All resource submissions require a valid session key (see **CreateSession**).
- Unauthroized submissions will recieve error code `401` (see **Errors**).

#### Problems
- method: **POST**
- endpoint: *api.rikerproject.com/problems*
- params:
	- `title`: String
	- `prompt`: String		-- *Parsed as markdown.*
	- `testInput`: String
	- `testOutput`: String
	- `timeout`: Int		-- *In seconds. Must be between 1 and 10 seconds.*
- response-body: N/A
- description: 
	Submits a problem. 

#### Solutions
- method: **POST**
- endpoint: *api.rikerproject.com/solutions*
- params:
	- `problemID`: Int
	- `title`: String
	- `language`: String
	- `source`: String
- response-body: N/A
- description: 
	Submits a solution to problem with id `problemID`.

#### ProblemComment
- method: **POST**
- endpoint: *api.rikerproject.com/problems/<problemId>/comments*
- params:
	- `sessionKey`: Int
	- `body`: String
response-body:
	{
		problemCommentId: Int
	}
description:
	Submits a comment for `problemId`.

#### SolutionComment
- method: **POST**
- endpoint: *api.rikerproject.com/solutions/<solutionId>/comments*
- params:
	- `sessionKey`: Int
	- `body`: String
response-body:
	{
		problemCommentId: Int
	}
description:
	Submits a comment for `problemId`. 


## Errors
- response-codes:
	`400`: Malformed or invalid request
	`401`: Authentication Error (invalid credientials or session key)
- response-body:
	{
		`errorMsg`: String
	}

