Riker.Problem = React.createClass({
	getInitialState: function() {
		return {
			errorMsg: ''
		};
	},
	handleError: function(msg) {
		this.setState({errorMsg: msg});
	},
	getProblem: function() {
		$.ajax({
			url: Riker.getApiEndpoint('problems/' + this.props.problemId),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.setState({
					title: data.title,
					prompt: data.prompt,
					userId: data.userId,
					submissionTime: data.submissionTime,
					timeout: data.timeout
				});
				console.log(data);
			}.bind(this),
			error: function(xhr, status, err) {
				var responseBody = $.parseJSON(xhr.responseText);
				this.handleError(responseBody.errorMsg);
			}.bind(this)
		});
	},
	componentDidMount: function() {
		this.getProblem();
	},
	render: function() {
		if (this.state.errorMsg == '') {
			return (
				<div>
					<h2>{this.state.title}</h2>
					<p>author: <a href={'/user/' + this.state.userId}>{this.state.userId}</a></p> 
					<p>submitted <em>{this.state.submissionTime}</em></p>
					<p><strong>Timeout: </strong> {this.state.timeout} second(s)</p>
					<h3>Prompt</h3>
					<p>{this.state.prompt}</p>
					<a href={'/problems/' + this.props.problemId + '/submit-solution'}>submit solution</a>
				</div>
			);
		}
		else {
			return (
				<p>{this.state.errorMsg}</p>
			);
		}
	}
});

