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
	Creates a user account.

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
	All resource submissions/edits/removals require a valid session key.
	Unauthroized submission/edits/removals will recieve error code `401` (see **Errors**).
		
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

#### Solutions
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
		`problemCommentId`: String,
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
		`solutionCommentId`: String,
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
		`problemCommentId`: String
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
		`solutionCommentId`: Int,
		`userId`: String,
		`submissionTime`: String,
		`solutionId`: Int,
		`body`: String
	}]
- description:
	Retrieves solution comments for `solutionId` by `userId` ordered by `submissionTime`.


## Resource Submissions

#### Problems
- method: **POST**
- endpoint: *api.rikerproject.com/problems*
- params:
	- `sessionKey`: String
	- `title`: String
	- `prompt`: String	
	- `testInput`: String
	- `testOutput`: String
	- `timeout`: Int		
- response-body: N/A
- description: 
	Submits a problem. `timeout` is in seconds.

#### Solutions
- method: **POST**
- endpoint: *api.rikerproject.com/solutions*
- params:
	- `sessionKey`: String
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
	- `sessionKey`: String
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
	- `sessionKey`: String
	- `body`: String
response-body:
	{
		problemCommentId: Int
	}
description:
	Submits a comment for `problemId`. 

## Resource Editing

#### EditProblem
- method: **POST**
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
- method: **POST**
- endpoint: *api.rikerproject.com/solutions/<solution_id>/edit*
- params:
	- `sessionKey`: String
	- `problemID`: Int
	- `title`: String
	- `language`: String
	- `source`: String
- response-body: N/A
description:
	Updates the fields of `solutionId`.

#### EditProblemComment
- method: *POST*
- endpoint: *api.rikerproject.com/problem-comments/<problemCommentId>/edit*
- params:
	- `sessionId`: String
	- `body`: String
- response-body: N/A
description:
	Updates contents of `problemCommentId`.
	
#### EditSolutionComment
- method: *POST*
- endpoint: *api.rikerproject.com/solution-comments/<solutionCommentId>/edit*
- params:
	- `sessionId`: String
	- `body`: String
- response-body: N/A
description:
	Updates contents of `problemCommentId`.
	

## Resource Removal

#### RemoveProblem
- method: *DELETE*
- endpoint: *api.rikerproject.com/problems/<problemId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `problemId` and all associated solutions/comments.

#### RemoveSolution
- method: *DELETE*
- endpoint: *api.rikerproject.com/solutions/<solutionId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `solutionId` and all associated comments.

#### RemoveProblemComment
- method: *DELETE*
- endpoint: *api.rikerproject.com/problem-comments/<problemCommentId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `problemCommentId`.

#### RemoveSolutionComment
- method: *DELETE*
- endpoint: *api.rikerproject.com/solution-comments/<solutionCommentId>*
- params:
	- `sessionKey`: String
- response-body: N/A
- description:
	Removes `solutionCommentId`. 


## Errors
- response-codes:
	- `400`: Malformed or invalid request
	- `401`: Authentication error (invalid credientials or session key)
- response-body:
	{
		`errorMsg`: String
	}

