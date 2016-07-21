Riker.Solution = React.createClass({
	getInitialState: function() {
		return {
			errorMsg: ''
		};
	},
	handleError: function(msg) {
		this.setState({errorMsg: msg});
	},
	getProblemPrompt: function() {
		$.ajax({
			url: Riker.getApiEndpoint('problems/' + this.props.problemId),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.setState({
					prompt: data.prompt
				});
			}.bind(this),
			error: function(xhr, status, err) {
				responseBody = $.parseJSON(xhr.responseText);
				handleError(responseBody.errorMsg);
			}
		});
	},
	getSolution: function() {
		$.ajax({
			url: Riker.getApiEndpoint('solutions/' + this.props.solutionId),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.setState({
					userId: data.userId,
					submissionTime: data.submissionTime,
					language: data.language,
					verification: data.verification,
					source: data.source
				});
			}.bind(this),
			error: function(xhr, status, err) {
				var responseBody = $.parseJSON(xhr.responseText);
				this.handleError(responseBody.errorMsg);
			}.bind(this)
		});
	},
	componentDidMount: function() {
		this.getProblemPrompt();
		this.getSolution();
		hljs.initHighlighting();
	},
	render: function() {
		return (
			<div>
				<h3>Prompt</h3>
				<p>{this.state.prompt}</p>
				<h3>Solution</h3>
				<p>
					author: <em>{this.state.userId}</em><br/>
					language: <em>{this.state.language}</em><br/>
					submission time: <em>{this.state.submissionTime}</em><br/>
					verification: <em>{this.state.verification}</em><br/>
				</p>
				<pre><code className={this.state.language}>{this.state.source}</code></pre>
				<p>{this.state.errorMsg}</p>
			</div>
		);
	}
});

