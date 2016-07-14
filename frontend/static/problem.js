Riker.Problem = React.createClass({
	getInitialState: function() {
		return {};
	},
	handleError: function(msg) {
		this.state.errorMsg = msg;
	},
	componentDidMount: function() {
		$.ajax({
			url: Riker.getApiEndpoint('problems/' + this.props.problemId),
			dataType: 'json',
			type: 'GET',
			success: function(data) {
				this.setState({
					title: data.title,
					prompt: data.prompt,
					userId: data.userId,
					submissionTime: data.submissionTime
				});
			}.bind(this),
			error: function(xhr, status, err) {
				responseBody = $.parseJSON(xhr.responseText);
				handleError(responseBody.errorMsg);
			}
		});
	},
	render: function() {
		if (this.state.title) {
			return (
				<div>
					<h2>{this.state.title}</h2>
					<p>author: <a href={'/user/' + this.state.userId}>{this.state.userId}</a></p> 
					<p>submitted <em>{this.state.submissionTime}</em></p>
					<h3>Prompt</h3>
					<p>{this.state.prompt}</p>
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

